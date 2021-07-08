from rumboot.chipDb import ChipDb
from rumboot.ImageFormatDb import ImageFormatDb
from rumboot.resetSeq import ResetSeqFactory
from rumboot.cmdline import arghelper
from rumboot.terminal import terminal
import os
import sys
import argparse
import rumboot_xrun
import rumboot
from parse import *
import atexit
import threading
import time


# TODO & questions:
# - Timeout handling in tests
# - Is atexit a good way to call the actual testing?
# - Decorator & class instance registration methods
# - Helper functions to add tests from directory
# - GUI integration

class RumbootTestBase(threading.Thread):
    terminal = None

    def prepare(self, terminal):
        self.terminal = terminal

    def run(self):
        return self.execute(self.terminal)


class RumbootTestFacility():
    runlist = []
    def __init__(self):
        pass
    
    def register(self, test):
        self.runlist.append(test())

    def run(self, terminal, reset):
        for r in self.runlist:
            reset.resetToHost()
            r.prepare(terminal)
            r.start()
            print("test done", r.join())


__g_facility = RumbootTestFacility()


def RumbootTest(arg):
    print("Registering test", arg)
    __g_facility.register(arg)


def intialize_testing(target_chip=None):
    resets  = ResetSeqFactory("rumboot.resetseq")
    formats = ImageFormatDb("rumboot.images")
    chips   = ChipDb("rumboot.chips")
    c       = chips[target_chip] 

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-factorytest {} - RumBoot Board Testing Framework\n".format(rumboot.__version__) +
                                    rumboot.__copyright__)
    helper = arghelper()

    helper.add_terminal_opts(parser)
    helper.add_resetseq_options(parser, resets)

    opts = parser.parse_args()

    dump_path = os.path.dirname(__file__) + "/romdumps/"

    helper.detect_terminal_options(opts, c)

    print("Detected chip:    %s (%s)" % (c.name, c.part))
    if c == None:
        print("ERROR: Failed to auto-detect chip type")
        return 1
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
    print("--- --- --- --- --- --- ")

    return term, reset



@atexit.register
def execute():
    term, reset = intialize_testing("mm7705")
    __g_facility.run(term, reset)
