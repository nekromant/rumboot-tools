from rumboot.chipDb import ChipDb
from rumboot.ImageFormatDb import ImageFormatDb
from rumboot.resetSeq import ResetSeqFactory
from rumboot.cmdline import arghelper
from rumboot.terminal import terminal

import os
import argparse
import rumboot_xflash
import rumboot_packimage
from parse import *
import rumboot

def cli():
    resets  = ResetSeqFactory("rumboot.resetseq")
    formats = ImageFormatDb("rumboot.images")
    chips   = ChipDb("rumboot.chips")

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-xflash {} - RumBoot X-Modem firmware update tool\n".format(rumboot.__version__) +
                                    rumboot.__copyright__)
    helper = arghelper();                                
    helper.add_file_handling_opts(parser, True)
    helper.add_terminal_opts(parser)
    parser.add_argument("-v", "--verbose", 
                        default=False,
                        action='store_true',
                        help="Print serial debug messages during update"),
    parser.add_argument("-m", "--memory",
                        help="Memory program. Help for a list of memories",
                        nargs=1, metavar=('memory'),
                        default="help",
                        required=True)                        
    parser.add_argument("-z", "--spl-path",
                        help="Path for SPL writers (Debug only)",
                        type=str,
                        required=False)

    helper.add_resetseq_options(parser, resets)

    opts = parser.parse_args()

    chip, term, reset = helper.create_core_stuff_from_options(opts)

    mem = opts.memory[0]
    if not mem:
        return 1

    if mem == "help":
        for mem,spl in chip.memories.items():
            print("Memory %16s: %s" % (mem, spl))
        return 1


    #Open files, rebuild if needed
    opts.file[0], dumps = helper.process_files(opts.file[0], False)

    spl_path = os.path.dirname(__file__) + "/spl-tools/"

    try:
        spl = chip.memories[mem]
    except:
        print("ERROR: Target chip (%s) doesn't have memory '%s'. Run with -m help for a list" % (chip.name, mem))
        return 1

    if opts.spl_path != None:
        spl_path = opts.spl_path
        print("SPL                              %s" % (spl_path + chip.memories[mem]))

    spl = spl_path + chip.memories[mem]

    terminal.verbose = opts.verbose
    term.add_binaries(spl)
    term.add_binaries(opts.file[0][0])
    if opts.edcl and chip.edcl != None:
        term.xfer.selectTransport("edcl")

    try:
        reset.resetToHost()
    except:
        print("WARN: Reset method doesn't support HOST mode switching")
        print("WARN: If things don't work - check jumpers!")
        reset.reset()

    return term.loop()
