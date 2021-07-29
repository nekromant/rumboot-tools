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
        self.passwd = opts.apc_pass
        self.host   = opts.apc_host
        self.user   = opts.apc_user
        self.outlet = opts.apc_outlet


    def expect(self, f, inw, outw):
        failures = 0
        while True:
            if failures > 30:
                raise Exception("Problem with APC")
            tmp = f.readline()
            if len(tmp) == 0:
                sleep(0.1)
                failures += 1
                pass
            if inw in tmp:
                f.write(outw + "\r")
                f.flush()
                return

    def _power(self, on):
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
                 sleep(3) #Power bricks have huge caps. Let power stabilize

    def power(self, on):
        #Sometimes we can connect, but get back nothing
        retries = 4
        while True:
            try:
                self._power(on)
                break
            except:
                continue

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
