import os
from time import sleep
import socket
from rumboot.resetseq.resetSeqBase import base

class apc(base):
    name = "apc"
    host = "192.168.10.2"
    port = 23
    user = "whiteblade"
    passwd = "ash2wert"
    outlet = 8

    def __init__(self, opts):
        self.passwd = opts["apc-passwd"]
        self.host   = opts["apc-host"]
        self.user   = opts["apc-user"]
        self.outlet = opts["apc-outlet"]


    def expect(self, f, inw, outw):
        while True:
            tmp = f.readline()
            if len(tmp) == 0:
                sleep(0.2)
                pass
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
             sleep(2) #Power bricks have huge caps. Let power stabilize

    def resetWithCustomFlags(self, flags=[]):
        return self.resetToHost(flags)

    def resetToHost(self, flags = []):
        self.power(0)
        sleep(3)
        self.power(1)

    def resetToNormal(self, flags = []):
        self.power(0)
        sleep(3)
        self.power(1)

    def add_argparse_options(parser):
        parser.add_argument("--apc-host",
                            help="APC IP Address/hostname",
                            default="192.168.10.2",
                            required=False)
        parser.add_argument("--apc-user",
                            help="APC IP username",
                            default="whiteblade",
                            required=False)
        parser.add_argument("--apc-pass",
                            help="APC IP username",
                            default="ash2wert",
                            required=False)
        parser.add_argument("--apc-outlet",
                            help="APC power outlet to use",
                            default=8,
                            required=False)
