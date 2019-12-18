import serial
import sys
from xmodem import XMODEM
import os
from parse import parse
import time
import io
from tqdm import tqdm
from rumboot.OpFactory import OpFactory

class terminal:
        verbose=True
        logstream=None
        plusargs={}
        runlist = []

        def __init__(self, port, speed):
            self.port = port
            self.ser = serial.Serial(port, speed, timeout=5)
            def getc(size, timeout=10):
                ret = self.ser.read(size)
                return ret or None
            def putc(data, timeout=10):
                return self.ser.write(data)  # note that this ignores the timeout
            self.modem = XMODEM(getc, putc)
            self.opf = OpFactory("rumboot.ops", self) 


        def add_binaries(self, path):
            if type(path) is list:
                for p in path:
                    self.runlist.append(p[0])
            else:
                self.runlist.append(path)

        def next_binary(self):
            if len(self.runlist) > 0:
                return self.runlist.pop(0)
            return None

        def log(self, *args, **kwargs):
            # Sometimes we get a weird exception on certain windows systems/setups
            # Try to catch any exceptions and dispose of them here
            try:
                if self.verbose:
                    tqdm.write(*args, **kwargs)
                    sys.stdout.flush()
                if not self.logstream == None:
                    self.logstream.write(*args)
            except:
                pass

        def loop(self, exitfmt="boot: host: Back in rom, code {}"):
            while True:
                ret = None
                line = self.ser.readline()
                if line == b'':
                    continue
                try: 
                    line = line.decode().rstrip()
                except:
                    continue

                self.log(line, end='\n')
                ret = self.opf.handle_line(line)
                if type(ret) is int:
                    return ret

 
        def xmodem_send(self, fl, chunksize=0, desc="Uploading file", welcome=b"boot: host: Hit 'X' for xmodem upload\n"):
            stream = open(fl, 'rb')
            ret = self.xmodem_send_stream(stream, chunksize, welcome, desc)
            stream.close()
