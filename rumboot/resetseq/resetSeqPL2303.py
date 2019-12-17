import os
import time
from rumboot.resetseq.resetSeqBase import base
class pl2303(base):
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

    def __init__(self):
        self.port = -1

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

    def add_argparse_options(parser):
        parser.add_argument("-P", "--pl2303-port",
                            help="PL2303 physical port (for -P of pl2303gpio)",
                            nargs=1, metavar=('value'),
                            default=[ "-1" ],
                            required=False)
        parser.add_argument("--pl2303-invert",
                            help="Invert all pl2303 gpio signals",
                            action='store_true',
                            required=False)



#class pl2303i(pl2303):
#    invert = 1
#    name = "pl2303 (inverted)"