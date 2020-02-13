import os
import time
from rumboot.resetseq.resetSeqBase import base
class pl2303(base):
    name = "pl2303"
    #Physical port to use
    port = -1
    invert = False
    # GPIO0: reset
    # GPIO1: power

    def gpio(self, gp, v):
        if self.invert:
            v = not v
        os.system("pl2303gpio --port=%d --gpio=%d --out=%d" % (self.port, gp, v))

    def __init__(self, opts):
        self.port   = int(opts.pl2303_port[0])
        self.invert = opts.pl2303_invert

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
                            default = False,
                            required=False)
