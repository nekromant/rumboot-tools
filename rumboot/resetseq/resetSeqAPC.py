import os
from time import sleep
import socket
from rumboot.resetseq.resetSeqBase import base

class apc(base):
    name = "APC Switched Racked PDU"
    host = "192.168.10.2"
    port = 23
    user = "whiteblade"
    passwd = "ash2wert"
    outlet = 8

    def __init__(self, terminal, opts):
        self.passwd = opts["apc_pass"]
        self.host   = opts["apc_host"]
        self.user   = opts["apc_user"]
        self.outlet = opts["apc_outlet"]
        super().__init__(terminal,opts)

    def __expect(self, f, inw, outw):
        failures = 0
        while True:
            if failures > 30:
                raise Exception("APC didn't reply in time")
            tmp = f.readline()
            if len(tmp) == 0:
                sleep(0.1)
                failures += 1
                pass
            if inw in tmp:
                f.write(outw + "\r")
                f.flush()
                return

    def __power(self, on):
            s = socket.create_connection((self.host, self.port), timeout=3)
            s.setblocking(0)
            if on:
                on = 1
            else:
                on = 2
            f = s.makefile('rw', encoding="ascii", errors="replace", newline='\r')
            self.__expect(f, "User Name :", self.user)
            self.__expect(f, "Password  :", self.passwd)
            self.__expect(f, ">", "1")
            self.__expect(f, ">", "2")
            self.__expect(f, ">", "1")
            self.__expect(f, ">", str(self.outlet))
            self.__expect(f, ">", str(on))
            self.__expect(f, "Enter 'YES' to continue or <ENTER> to cancel", "YES")
            self.__expect(f, "Press <ENTER> to continue...", "")
            s.close()
            sleep(3) #Power bricks have huge caps. Let power stabilize

    def power(self, on):
        #Sometimes we can connect, but get back nothing
        retries = 4
        while retries:
            try:
                self.__power(on)
                return
            except Exception as e:
                print(f"APC: APC Operation failed: {e}")
                retries = retries - 1
                continue
        raise Exception("APC: Too many APC operations failed, giving up")

    #We always rely on power-on reset
    def __setitem__(self, key, value):
        super().__setitem__(key, value)

        if key == "POWER":
            self.power(value)

        if key == "RESET":
            pass

    def get_options(self):
        return {
                "apc-host" : {
                    "help" : "APC IP Address/hostname",
                    "default" : "192.168.10.2",
                    "required": False
                },
                "apc-user" : {
                    "help" : "APC Username",
                    "default" : "whiteblade",
                    "required": False
                },
                "apc-pass" : {
                    "help" : "APC Password",
                    "default" : "ash2wert",
                    "required": False
                },
                "apc-outlet" : {
                    "help" : "APC Outlet Number",
                    "default" : 8,
                    "required": False
                }
            }