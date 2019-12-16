import os
import time
class resetSeqPL2303:
    name = "pl2303"
    #Physical port to use
    port = -1
    invert = 0
    # GPIO0: reset
    # GPIO1: power

    def gpio(self, gp, v):
        if self.invert:
            v = not v
        os.system("pl2303gpio --port=%d --gpio=%d --out=%d" % (self.port, gp, v))

    def __init__(self, port):
        self.port = port

    def resetWithCustomFlags(self, flags=[]):
        print("Please, power-cycle board")

    def resetToHost(self, flags = []):
        self.gpio(0, 1)
        self.gpio(1, 1)
        time.sleep(1)
        self.gpio(1, 0)
        self.gpio(0, 0)

    def resetToNormal(self, flags = []):
        self.gpio(0, 1)
        self.gpio(1, 1)
        time.sleep(1)
        self.gpio(1, 0)
        self.gpio(0, 0) 


class resetSeqPL2303i(resetSeqPL2303):
    invert = 1
    name = "pl2303 (inverted)"