import os
import time
import usb.core
import pygpiotools
import usb.util
from parse import parse
from rumboot.resetseq.resetSeqBase import base

class pl2303(base):
    name = "pl2303"
    invert = False
    swap   = False
    supported = ["POWER", "RESET"]
    mapping = {
        "POWER" : 0,
        "RESET" : 1
    }

    def __init__(self, terminal, opts):
        self.invert   = opts["pl2303_invert"]
        self.swap     = opts["pl2303_swap"]
        self.__handle = pygpiotools.connect_pyserial("pl2303", terminal.ser)

        if self.swap:
            tmp = self.mapping["POWER"]
            self.mapping["POWER"] = self.mapping["RESET"]
            self.mapping["RESET"] = tmp

        super().__init__(terminal, opts)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self.invert:
            value = not value
        pygpiotools.direction(self.__handle, self.mapping[key], "OUTPUT")
        pygpiotools.write(self.__handle, self.mapping[key], value)

    def get_options(self):
        return {
                "pl2303-invert" : {
                    "help" : "Invert all pl2303 gpio signals",
                    "default" : False,
                    "action"  : 'store_true'
                },
                "pl2303-swap" : {
                    "help" : "Invert all pl2303 gpio signals",
                    "default" : False,
                    "action"  : 'store_true'
                }

            }


#    def add_argparse_options(parser):
#        parser.add_argument("-P", "--pl2303-port",
#                            help="PL2303 physical port",
#                            nargs=1, metavar=('value'),
#                            required=False)
#        parser.add_argument("--pl2303-invert",
#                            help="Invert all pl2303 gpio signals",
#                            action='store_true',
#                            default = False,
#                            required=False)
