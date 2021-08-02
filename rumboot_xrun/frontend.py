from rumboot.cmdline import arghelper
from rumboot.resetSeq import ResetSeqFactory
import os
import sys
import argparse
import rumboot_xrun
import rumboot
from parse import *

def cli():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-xrun {} - RumBoot X-Modem execution tool\n".format(rumboot.__version__) +
                                    rumboot.__copyright__)
    helper = arghelper()
    resets  = ResetSeqFactory("rumboot.resetseq")
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

    chip, term, reset = helper.create_core_stuff_from_options(opts)

    term.plusargs = plusargs
    try:
        romdump = open(dump_path + chip.romdump, "r")
        term.add_dumps({'rom' : romdump})
    except:
        pass

    if opts.log:
        term.logstream = opts.log

    try:
        reset.resetToHost()
    except:
        print("WARN: Reset method doesn't support HOST mode switching")
        print("WARN: If things don't work - check jumpers!")
        reset.reset()

    term.add_binaries(opts.file)
    term.add_dumps(dumps)
    term.replay_till_the_end = opts.replay_no_exit

    return term.loop(opts.stdin)
