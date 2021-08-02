import os
import time
import usb.core
import pygpiotools
import usb.util
from parse import parse
from rumboot.resetseq.resetSeqBase import base

class pl2303(base):
    name = "PL2303HX"
    swap   = False
    supported = ["POWER", "RESET"]
    mapping = {
        "POWER" : 0,
        "RESET" : 1
    }

    def __init__(self, terminal, opts):
        self.invert_power   = opts["pl2303_invert_power"]
        self.invert_reset   = opts["pl2303_invert_reset"]
        self.swap           = opts["pl2303_swap"]
        self.__handle = pygpiotools.connect_pyserial("pl2303", terminal.ser)

        if self.swap:
            tmp = self.mapping["POWER"]
            self.mapping["POWER"] = self.mapping["RESET"]
            self.mapping["RESET"] = tmp

        super().__init__(terminal, opts)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self.invert_power and key == "POWER":
            value = not value
        if self.invert_reset and key == "RESET":
            value = not value

        pygpiotools.direction(self.__handle, self.mapping[key], "OUTPUT")
        pygpiotools.write(self.__handle, self.mapping[key], value)

    def get_options(self):
        return {
                "pl2303-invert-reset" : {
                    "help" : "Invert pl2303 reset signal",
                    "default" : False,
                    "action"  : 'store_true'
                },
                "pl2303-invert-power" : {
                    "help" : "Invert pl2303 power signal",
                    "default" : False,
                    "action"  : 'store_true'
                },
                "pl2303-swap" : {
                    "help" : "Swap pl2303 reset and power mapping",
                    "default" : False,
                    "action"  : 'store_true'
                }
            }