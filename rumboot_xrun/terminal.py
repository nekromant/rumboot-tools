import serial
import sys
from xmodem import XMODEM
import os
from parse import parse
import time
import io

class terminal:
        def __init__(self, port, speed):
            self.port = port
            self.ser = serial.Serial(port, speed, timeout=1)
            def getc(size, timeout=10):
                ret = self.ser.read(size)
                return ret or None
            def putc(data, timeout=10):
                return self.ser.write(data)  # note that this ignores the timeout
            self.modem = XMODEM(getc, putc)

        def loop(self, exitfmt="boot: host: Back in rom, code {}"):
            while True:
                ret = None
                line = self.ser.readline()
                try: 
                    line = line.decode()
                    print(line, end='')
                    ret = parse(exitfmt, line)
                except:
                    pass

                if ret:
                   code = ret[0]
                   return int(code)

        def poll_for_invite(self, welcome):
            while True:
                line = self.ser.readline()
                try: 
                    l = line.decode()
                    print(l,end='')
                except:
                    print(line, end='')
                if (line == welcome):
                    print("Got invitation!")
                    self.ser.write("X".encode())
                    while True:
                        tmp1 = self.ser.read(1)
                        tmp2 = self.ser.read(1)
                        if tmp1 == b"C" and tmp2 == b"C": 
                            print("Synchronized!")                            
                            break
                    break

        def xmodem_send(self, fl, chunksize=0, welcome=b"boot: host: Hit 'X' for xmodem upload\n"):
            stream = open(fl, 'rb')
            return self.xmodem_send_stream(stream, chunksize, welcome)

        def xmodem_send_stream(self, stream, chunksize=0, welcome=b"boot: host: Hit 'X' for xmodem upload\n"):
            self.poll_for_invite(welcome)
            stream.seek(0)
            if chunksize==0:
                ret = self.modem.send(stream, retry=16)
            else:
                while True:
                    data = stream.read(chunksize)
                    if (not data):
                            break
                    data = io.BytesIO(data)
                    ret = self.modem.send(data, retry=16)
                    self.poll_for_invite(welcome)            
