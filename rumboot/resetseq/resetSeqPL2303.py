import os
import time
from parse import parse
from rumboot.resetseq.resetSeqBase import base
class pl2303(base):
    name = "pl2303"
    #Physical port to use
    port = -1
    invert = False
    # GPIO0: power
    # GPIO1: reset

    def gpio(self, gp, v):
        if self.invert:
            v = not v
        os.system("pl2303gpio --port=%d --gpio=%d --out=%d" % (self.port, gp, v))

    def __init__(self, opts):
        self.invert = opts.pl2303_invert

        if opts.pl2303_port:
            self.port = opts.pl2303_port[0]
            return

        #Else - proceed with auto-detection
        try:
            dev = os.readlink(opts.port[0])
        except:
            dev = opts.port[0]

        tty = parse("/dev/ttyUSB{}", dev)
        if tty:
            dev = "ttyUSB" + tty[0]
        syspath = os.readlink("/sys/bus/usb-serial/devices/" + dev)
        syspath = syspath.split("/")
        devid = parse("{}.{}:{}", syspath[-2])
        if not devid:
            devid = parse("{}-{}:{}", syspath[-2])

        self.port = int(devid[1])
        print("pl2303: %s detected at physical port %d" % (opts.port[0], self.port))



    def resetWithCustomFlags(self, flags=[]):
        print("Please, power-cycle board")

    def power(self, on):
        if on:
            self.gpio(0, 0)
        else:
            self.gpio(0, 1)

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
                            required=False)
        parser.add_argument("--pl2303-invert",
                            help="Invert all pl2303 gpio signals",
                            action='store_true',
                            default = False,
                            required=False)
