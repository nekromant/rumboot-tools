import os
import sys
import argparse
import threading
import time

from parse import parse

from rumboot.chipDb import ChipDb
from rumboot.ImageFormatDb import ImageFormatDb
from rumboot.resetSeq import ResetSeqFactory
from rumboot.cmdline import arghelper
from rumboot.terminal import terminal
import rumboot_xrun
import rumboot


class engine():
    def __init__(self, target_chip=None, transport="xmodem", args=None):
        resets  = ResetSeqFactory("rumboot.resetseq")
        formats = ImageFormatDb("rumboot.images")
        chips   = ChipDb("rumboot.chips")
        c       = chips[target_chip] 

        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="Rumboot Scripting Engine script, using rumboot-tools {}\n".format(rumboot.__version__) +
                                        rumboot.__copyright__)
        helper = arghelper()

        helper.add_terminal_opts(parser)
        helper.add_resetseq_options(parser, resets)

        opts = parser.parse_args()

        dump_path = os.path.dirname(__file__) + "/romdumps/"

        helper.detect_terminal_options(opts, c)

        print("Target Chip:    %s (%s)" % (c.name, c.part))
        if c == None:
            raise Exception("ERROR: Failed to auto-detect chip type")

        if opts.baud == None:
            opts.baud = [ c.baudrate ]

        reset = resets[opts.reset[0]](opts)
        term = terminal(opts.port[0], opts.baud[0])
        term.set_chip(c)

        try:
            romdump = open(dump_path + c.romdump, "r")
            term.add_dumps({'rom' : romdump})
        except:
            pass

        if opts.log:
            term.logstream = opts.log

        print("Reset method:               %s" % (reset.name))
        print("Baudrate:                   %d bps" % int(opts.baud[0]))
        print("Port:                       %s" % opts.port[0])
        if opts.edcl and c.edcl != None:
            term.xfer.selectTransport("edcl")
        print("Preferred data transport:   %s" % term.xfer.how)
        print("--- --- --- --- --- --- --- --- --- ")
        self.terminal = term

    def reset(self):
        pass

    def run(self, spl, stdout=None):
        pass
    
    def read32(self, addr):
        pass

    def write32(self, addr, data):
        pass

    def read8(self, addr):
        pass

    def write8(self, addr, data):
        pass

    def read16(self, addr):
        pass

    def write16(self, addr, data):
        pass

    def read64(self, addr):
        pass

    def write64(self, addr, data):
        pass

    def dump(self, addr, len):
        pass

    def upload(self, file, addr):
        pass

    def download(self, file, addr, length):
        pass

