from rumboot_packimage import imageFormatBase
from rumboot_packimage import imageFormatV2
from rumboot_packimage import imageFormatLegacy
from rumboot_packimage import imageFormatElfV2
from rumboot_packimage import chipDb
from rumboot_xrun import resetSeqMT12505
from rumboot_xrun import resetSeqBase
from rumboot_xrun import resetSeqPL2303
from rumboot_xrun import resetSeqPowerHub
from rumboot_xrun import terminal

import argparse
import rumboot_packimage
import os


def guessImageFormat(file):
    formats = [ imageFormatElfV2.ImageFormatElfV2,
                imageFormatLegacy.ImageFormatLegacy,
                imageFormatV2.ImageFormatV2,
            ];
    for f in formats:
        tmp = f(file)
        if tmp.check():
            return tmp
    return False

def pickResetSequence(opts):
    if opts.reset[0] == "pl2303":
        return resetSeqPL2303.resetSeqPL2303(int(opts.pl2303_port[0]))
    if opts.reset[0] == 'mt12505':
        return resetSeqMT12505.resetSeqMT12505(opts.ft232_serial[0])
    if opts.reset[0] == 'powerhub':
        return resetSeqPowerHub.resetSeqPowerHub(opts.ft232_serial[0])
    return resetSeqBase.resetSeqBase()

def cli():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-xflash {} - RumBoot X-Modem firmware update tool\n".format(rumboot_packimage.__version__) +
                                    "(C) 2018-2019 Andrew Andrianov, RC Module\nhttps://github.com/RC-MODULE")

    parser.add_argument("-f", "--file",
                        help="image file to write",
                        type=argparse.FileType("rb"),
                        required=False)
    parser.add_argument("-c", "--chip_id",
                        help="Override chip id",
                        nargs=1, metavar=('chip_id'),
                        required=False)
    parser.add_argument("-l", "--log",
                        help="Log terminal output to file",
                        type=argparse.FileType("wb+"),
                        required=False)
    parser.add_argument("-p", "--port",
                        help="Serial port to use",
                        nargs=1, metavar=('value'),
                        default=["/dev/ttyUSB0"],
                        required=False)
    parser.add_argument("-b", "--baud",
                        help="Serial port to use e.g. /dev/ttyUSB0 (*nix), com1: (windows)",
                        nargs=1, metavar=('port'),
                        required=False)
    parser.add_argument("-r", "--reset",
                        help="Reset sequence to use (none, pl2303, mt12505)",
                        nargs=1, metavar=('sequence'),
                        default="none",
                        required=False)
    parser.add_argument("-v", "--verbose", 
                        help="Print serial debug messages during update"),
    parser.add_argument("-m", "--memory",
                        help="Memory program. Help for a list of memories",
                        nargs=1, metavar=('memory'),
                        default="help",
                        required=True)                        
    parser.add_argument("-S", "--ft232-serial",
                        help="FT232 serial number for MT125.05",
                        nargs=1, metavar=('serial'),
                        default="A92XPFQL",
                        required=False)
    parser.add_argument("-P", "--pl2303-port",
                        help="PL2303 physical port (for -P of pl2303gpio)",
                        nargs=1, metavar=('value'),
                        default=[ "-1" ],
                        required=False)
    parser.add_argument("-z", "--spl-path",
                        help="Path for SPL writers (Debug only)",
                        type=str,
                        required=False)

    opts = parser.parse_args()

    spl_path = os.path.dirname(__file__) + "/spl-tools/"
    
    if opts.file:
        t = guessImageFormat(opts.file)
        if t == False and opts.chip_id == None:
            print("Failed to detect image format")
            return 1

    db = chipDb.chipDb()

    if opts.chip_id == None:
        c = db.query(t.get_chip_id(),t.get_chip_rev())
    else:        
        c = db.query(int(opts.chip_id[0]), 1)

    if c == None:
        print("ERROR: Failed to auto-detect chip type")
        return 1
    if opts.baud == None:
        opts.baud = [ c.baudrate ]

    print("Detected chip:    %s (%s)" % (c.name, c.part))    
    if hasattr(c,"warning"):
        print("    --- WARNING ---")
        print(c.warning)        
        print("    --- WARNING ---")
        print("")

    reset = pickResetSequence(opts)
    term = terminal.terminal(opts.port[0], opts.baud[0])

    if opts.log:
        term.logstream = opts.log

    if opts.verbose == None:
        term.verbose = False

    mem = opts.memory[0]
    if not mem:
        return 1

    if mem == "help":
        for mem,spl in c.memories.items():
            print("Memory %16s: %s" % (mem, spl))
        return 1

    try:
        spl = c.memories[mem]
    except:
        print("ERROR: Target chip (%s) doesn't have memory '%s'. Run with -m help for a list" % (c.name, mem))
        return 1

    if opts.spl_path != None:
        spl_path = opts.spl_path
        print("SPL               %s" % (spl_path + c.memories[mem]))

    spl = spl_path + c.memories[mem]

    print("Reset method:     %s" % (reset.name))
    print("Baudrate:         %d bps" % int(opts.baud[0]))
    print("Port:             %s" % opts.port[0])
    reset.resetToHost()
    term.xmodem_send(spl, desc="Uploading SPL")
    print("Preparing image upload, please stand by...")
    term.xmodem_send_stream(opts.file, 0, b"boot: Press 'X' and send me the image\n", desc="Writing image")
    reset.resetToNormal()
    term.loop()
    
