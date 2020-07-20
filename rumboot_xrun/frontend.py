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

def cli():
    resets  = ResetSeqFactory("rumboot.resetseq")
    formats = ImageFormatDb("rumboot.images")
    chips   = ChipDb("rumboot.chips")

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-xrun {} - RumBoot X-Modem execution tool\n".format(rumboot.__version__) +
                                    rumboot.__copyright__)
    helper = arghelper()

    helper.add_file_handling_opts(parser, True)
    helper.add_terminal_opts(parser)
    helper.add_resetseq_options(parser, resets)
    plus = parser.add_argument_group("Plusargs parser options",
        """
        rumboot-xrun can parse plusargs (similar to verilog simulator)
        and use them for runtime file uploads. This option is intended
        to be used for
        """)
    plus.add_argument('-A', '--plusargs', nargs='*')
    parser.add_argument("-R", "--rebuild",
                        help="Attempt to rebuild/update target before uploading",
                        action="store_true",
                        default=False,
                        required=False)

    parser.add_argument("-I", '--stdin',
                        help="Use stdin redirection to tty",
                        action="store_true",
                        default=False,
                        required=False)
    parser.add_argument('--replay-no-exit',
                        help="Do not exit on panics/rom returns when replaying logs (for batch analysis)",
                        action="store_true",
                        default=False,
                        required=False)
    if len(sys.argv) == 1:
        sys.argv = sys.argv + ["--help"]

    opts = parser.parse_args()

    #Open files, rebuild if needed
    opts.file[0], dumps = helper.process_files(opts.file[0], opts.rebuild)

    dump_path = os.path.dirname(__file__) + "/romdumps/"

    plusargs = {}
    if opts.plusargs:
        for a in opts.plusargs:
            ret = parse("+{}={}", a)
            if ret:
                plusargs[ret[0]] = ret[1]
                continue
            ret = parse("+{}", a)
            if ret:
                plusargs[ret[0]] = True

    c = helper.detect_chip_type(opts, chips, formats)
    if c == None:
        return 1

    print("Detected chip:    %s (%s)" % (c.name, c.part))
    if c == None:
        print("ERROR: Failed to auto-detect chip type")
        return 1
    if opts.baud == None:
        opts.baud = [ c.baudrate ]

    reset = resets[opts.reset[0]](opts)
    term = terminal(opts.port[0], opts.baud[0])
    term.set_chip(c)
    term.plusargs = plusargs
    term.xfer.xfers["edcl"].force_static_arp = opts.force_static_arp

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
    reset.resetToHost()
    term.add_binaries(opts.file)
    term.add_dumps(dumps)
    term.replay_till_the_end = opts.replay_no_exit
    if opts.edcl and c.edcl != None:
        term.xfer.selectTransport("edcl")
    print("Preferred data transport:   %s" % term.xfer.how)
    return term.loop(opts.stdin)
