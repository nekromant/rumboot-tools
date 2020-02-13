from rumboot.chipDb import ChipDb
from rumboot.ImageFormatDb import ImageFormatDb
from rumboot.resetSeq import ResetSeqFactory
from rumboot.cmdline import arghelper
from rumboot.terminal import terminal
from rumboot.server import server
import os
import argparse
import rumboot_xrun
from parse import *

def cli():
    resets  = ResetSeqFactory("rumboot.resetseq")
    formats = ImageFormatDb("rumboot.images")
    chips   = ChipDb("rumboot.chips")

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-daemon {} - Collaborative board access daemon\n".format(rumboot_xrun.__version__) +
                                    "(C) 2018-2020 Andrew Andrianov, RC Module\nhttps://github.com/RC-MODULE")
    arghelper.add_terminal_opts(parser)
    arghelper.add_resetseq_options(parser, resets)
    parser.add_argument("-c", "--chip_id",
                        help="Specify target chip id (by name or chip_id)",
                        nargs=1, metavar=('chip_id'),
                        required=False)   
    parser.add_argument("-L", "--listen",
                        help="Specify address:port to listen (default 0.0.0.0:10000)",
                        nargs=1, metavar=('listen'), default="0.0.0.0:10001",
                        required=False)
    opts = parser.parse_args()

    c = arghelper.detect_chip_type(opts, chips, formats)
    if c == None:
        c = chips["chipBasis"]
        
    print("Detected chip:    %s (%s)" % (c.name, c.part))
    if c == None:
        print("ERROR: Failed to auto-detect chip type")
        return 1
    if opts.baud == None:
        opts.baud = [ c.baudrate ]

    reset = resets[opts.reset[0]]()

    if opts.log:
        term.logstream = opts.log

    print("Reset method:     %s" % (reset.name))
    print("Baudrate:         %d bps" % int(opts.baud[0]))
    print("Serial Port:      %s" % opts.port[0])
    print("Listen address:   %s" % opts.listen[0])
    reset.resetToHost()



    #term = terminal(opts.port[0], opts.baud[0])
    srv = server(opts.port[0], opts.baud[0], opts.listen[0])
    srv.set_reset_seq(reset)
    if "file" in opts:
        srv.add_binaries(opts.file)

    return srv.loop()
    
