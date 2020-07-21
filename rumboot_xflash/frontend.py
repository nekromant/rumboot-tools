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

    c = helper.detect_chip_type(opts, chips, formats)
    if (c == None):
        return 1;

    mem = opts.memory[0]
    if not mem:
        return 1

    if mem == "help":
        for mem,spl in c.memories.items():
            print("Memory %16s: %s" % (mem, spl))
        return 1


    #Open files, rebuild if needed
    opts.file[0], dumps = helper.process_files(opts.file[0], False)

    print("Detected chip:    %s (%s)" % (c.name, c.part))
    if c.warning != None:
        print("    --- WARNING ---")
        print(c.warning)        
        print("    --- WARNING ---")
        print("")

    spl_path = os.path.dirname(__file__) + "/spl-tools/"

    if opts.baud == None:
        opts.baud = [ c.baudrate ]

    reset = resets[opts.reset[0]](opts)
    term = terminal(opts.port[0], opts.baud[0])
    term.set_chip(c)
    if opts.log:
        term.logstream = opts.log
    
    term.verbose = opts.verbose
    term.xfer.xfers["edcl"].force_static_arp = opts.force_static_arp

    try:
        spl = c.memories[mem]
    except:
        print("ERROR: Target chip (%s) doesn't have memory '%s'. Run with -m help for a list" % (c.name, mem))
        return 1

    if opts.spl_path != None:
        spl_path = opts.spl_path
        print("SPL                              %s" % (spl_path + c.memories[mem]))

    spl = spl_path + c.memories[mem]

    print("Reset method:                    %s" % (reset.name))
    print("Baudrate:                        %d bps" % int(opts.baud[0]))
    print("Port:                            %s" % opts.port[0])

    reset.resetToHost()
    term.add_binaries(spl)
    term.add_binaries(opts.file[0][0])
    if opts.edcl and c.edcl != None:
        term.xfer.selectTransport("edcl")
    print("Preferred data transport:        %s" % term.xfer.how)

    reset.resetToHost()
    term.loop()
