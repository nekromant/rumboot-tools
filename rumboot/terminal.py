import serial
import sys
from xmodem import XMODEM
import os
from parse import parse
import time
import io
from tqdm import tqdm
from rumboot.OpFactory import OpFactory
from rumboot.chips.base import chipBase
from rumboot.ImageFormatDb import ImageFormatDb
from rumboot.edclManager import edclmanager
import socket
import select

if sys.platform != "win32":
	import tty
	import termios

class terminal:
        verbose=True
        logstream=None
        plusargs={}
        initial_loop_done = False
        runlist = []
        formats = ImageFormatDb("rumboot.images")
        chip = chipBase()
        dumps = {}
        curbin = "bootrom"
        progress = tqdm(disable=True)
        replay = False
        replay_till_the_end = False
        ser = None
        edcl = None
        mode = "xmodem"

        def __init__(self, port, speed, use_1k = False):
            self.port = port
            self.speed = speed
            if use_1k:
                self.mode = "xmodem1k"
            self.reopen()

        def edcl_enabled(self):
            return self.edcl != None
            
        def serial(self):
            return self.ser

        def reopen(self):
            if self.ser != None:
                self.ser.close()
                self.ser = None

            if self.port.find("file://") == 0:
                self.ser = open(self.port.replace("file://",""), "rb+")
                self.replay = True
            elif self.port.find("://") < 0:
                self.ser = serial.Serial(self.port, self.speed, timeout=5)
            else:
                self.ser = serial.serial_for_url(self.port, timeout=5)

            def getc(size, timeout=10):
                ret = self.ser.read(size)
                return ret or None
            def putc(data, timeout=10):
                return self.ser.write(data)  # note that this ignores the timeout
            self.modem = XMODEM(getc, putc, mode=self.mode)
            self.opf = OpFactory("rumboot.ops", self) 


        def set_chip(self, chip):
            self.chip = chip

        def tqdm(self, *args, **kwargs):
            self.progress.close()
            self.progress = tqdm(*args, **kwargs)

        def add_binaries(self, path):
            if type(path) is list:
                for p in path:
                    self.runlist.append(p[0])
            else:
                self.runlist.append(path)

        def add_dumps(self, dumps):
            self.dumps.update(dumps)

        def next_binary(self):
            if len(self.runlist) > 0:
                ret = self.runlist.pop(0)                
                self.curbin = ret
                return ret
            return None

        def current_binary(self):
            return self.curbin

        def current_dump(self):
            if self.curbin == "bootrom":
                return self.dumps["rom"]
            if self.curbin.name in self.dumps:
                return self.dumps[self.curbin.name]

        def log(self, skipecho, *args, **kwargs):
            # Sometimes we get a weird exception on certain windows systems/setups
            # Try to catch any exceptions and dispose of them here
            try:
                if not skipecho and self.verbose:
                    self.progress.write(*args, **kwargs)
                    sys.stdout.flush()
                if not self.logstream == None:
                    self.logstream.write(*args)
                    self.logstream.write("\n")
            except:
                pass


        def sync(self):
            if not self.replay:
                self.ser.reset_input_buffer()
            c1 = b'a'
            c2 = b'd'
            while True:
                c2 = self.ser.read(1)
                if c1 == b'U' and c2 == b'\r':
                    break
                if c1 == b'U' and c2 == b'\n':
                    break
                c1 = c2

        def hack(self, name):
            if name in self.chip.hacks and self.chip.hacks[name]:
                return True
            return False

        def enable_edcl(self):
            self.edcl = edclmanager()
            if not self.edcl.connect(self.chip):
                sys.exit(1)

        def loop(self, use_stdin=False, break_after_uploads=False):
            if not self.initial_loop_done:
                self.initial_loop_done = True
                self.opf.on_start()

            return_code = 0

            if use_stdin:
                old_settings = termios.tcgetattr(sys.stdin)
            try:
                if use_stdin:
                    tty.setcbreak(sys.stdin.fileno())

                if not self.hack("skipsync"):
                    self.sync()
                while True:
                    ret = None
                    if use_stdin : 
                        line = b''
                        sym = b''
                        while sym != b'\n':
                            if select.select([self.ser], [], [], 0) == ([self.ser], [], []):
                                sym = self.ser.read(1)
                                line = line + sym
                                sys.stdout.write(str(sym, 'utf-8', errors='replace'))
                                sys.stdout.flush()
                            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                                insym = sys.stdin.read(1)
                                self.ser.write(insym.encode())
                    else:
                        line = self.ser.readline()

                    if line == b'':
                        continue
                    try: 
                        line = line.decode().rstrip()
                    except:
                        continue

                    ret = self.opf.handle_line(line, use_stdin)
                    if type(ret) is int:
                        if not self.replay_till_the_end:
                            return ret
                        else:
                            return_code = ret
                    
                    if break_after_uploads and len(self.runlist) == 0:
                        break

                    if self.replay:
                        if (self.ser.tell() == os.fstat(self.ser.fileno()).st_size):
                            print("== END OF LOG REACHED ==")
                            break
            finally:
                if use_stdin:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    return return_code
 
        def xmodem_send(self, fl, chunksize=0, desc="Uploading file", welcome=b"boot: host: Hit 'X' for xmodem upload\n"):
            stream = open(fl, 'rb')
            ret = self.xmodem_send_stream(stream, chunksize, welcome, desc)
            stream.close()
