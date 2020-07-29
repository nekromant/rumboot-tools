import os
import sys
import argparse
import threading
import time

from parse import parse
from hexdump import hexdump

from rumboot.chipDb import ChipDb
from rumboot.ImageFormatDb import ImageFormatDb
from rumboot.resetSeq import ResetSeqFactory
from rumboot.cmdline import arghelper
from rumboot.terminal import terminal
import rumboot_xrun
import rumboot

#TODO: Passthrough all missing methods to self.xfer
#TODO: Preload sio spl, when required
#TODO: Implement missing API in xfer.py for edcl and serial

class engine():
    def preload(self):
        self.reset()

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
        self.xfer = term.xfer

    def reset(self):
        self.reset.resetToHost()

    #TODO: stdout processing
    def run(self, spl, stdout=None):
        self.term.add_binaries(spl)
        self.terminal.add_binaries(spl)
        return self.terminal.loop(False,True)

    def read32(self, addr):
        return self.xfer.read32(addr)

    def write32(self, addr, data):
        return self.xfer.write32(addr, data)

    def read8(self, addr):
        return self.xfer.read8(addr)

    def write8(self, addr, data):
        return self.xfer.write8(addr,data)

    def read16(self, addr):
        return self.xfer.read16(addr)

    def write16(self, addr, data):
        return self.xfer.write16(addr,data)

    def read64(self, addr):
        return self.xfer.read64(addr)

    def write64(self, addr, data):
        return self.xfer.write64(addr,data)

    def read(self, addr, len):
        return self.xfer.read(addr, len)

    def write(self, addr, data):
        return self.xfer.write(addr, data)

    def dump(self, addr, len):
        data = self.read(addr, len)
        hexdump(data)

    def upload(self, file, addr):
        pass

    def download(self, file, addr, length):
        pass
