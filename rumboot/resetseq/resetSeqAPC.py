import os
import time
import socket
from rumboot.resetseq.resetSeqBase import base

class apc(base):
    name = "apc"
    host = "elvenblade"
    port = 23
    user = "whiteblade"
    passwd = "ash2wert"
    outlet = 8

    def __init__(self, opts):
        pass


    def expect(self, f, inw, outw):
        while True:
            tmp = f.readline()
            if len(tmp) == 0:
                time.sleep(0.2)
                pass
            print(tmp, end='')
            if inw in tmp:
                f.write(outw + "\r")
                f.flush()
                return

    def power(self, on):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
             s.connect((self.host, self.port))
             s.setblocking(0)
             if on:
                 on = 1
             else:
                 on = 2
             f = s.makefile('rw', encoding="ascii", errors="replace", newline='\r')
             self.expect(f, "User Name :", self.user)
             self.expect(f, "Password  :", self.passwd)
             self.expect(f, ">", "1")
             self.expect(f, ">", "2")
             self.expect(f, ">", "1")
             self.expect(f, ">", str(self.outlet))
             self.expect(f, ">", str(on))
             self.expect(f, "Enter 'YES' to continue or <ENTER> to cancel", "YES")
             self.expect(f, "Press <ENTER> to continue...", "")
             s.close()

    def resetWithCustomFlags(self, flags=[]):
        print("Please, power-cycle board")

    def resetToHost(self, flags = []):
        self.power(0)
        self.power(1)

    def resetToNormal(self, flags = []):
        self.power(0)
        self.power(1)

    def add_argparse_options(parser):
        parser.add_argument("--apc-ip",
                            help="APC IP Address/hostname",
#                            default="192.168.10.2",
                            default="elvenblade",
                            required=False)
        parser.add_argument("--apc-user",
                            help="APC IP username",
                            default="whiteblade",
                            required=False)
        parser.add_argument("--apc-pass",
                            help="APC IP username",
                            default="ash2wert",
                            required=False)
        parser.add_argument("--apc-port",
                            help="APC Power port",
                            default=0,
                            required=False)
