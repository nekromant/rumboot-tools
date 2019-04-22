from rumboot_packimage import imageFormatBase
from rumboot_packimage import imageFormatV2
from rumboot_packimage import imageFormatLegacy
from rumboot_packimage import imageFormatElfV2
from rumboot_packimage import chipDb
from rumboot_xrun import resetSeqMT12505
from rumboot_xrun import resetSeqBase
from rumboot_xrun import terminal

import argparse
import rumboot_packimage


class RumbootXrun:
    """RumbootXrun tool frontend"""
    def __init__(self, opts):
        print("hello")

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


def cli():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-xrun {} - RumBoot X-Modem execution tool\n".format(rumboot_packimage.__version__) +
                                    "(C) 2018 Andrew Andrianov, RC Module\nhttps://github.com/RC-MODULE")
    parser.add_argument("-f", "--file",
                        help="image file",
                        type=argparse.FileType("rb"),
                        required=True)
    parser.add_argument("-p", "--port",
                        help="Serial port to use",
                        nargs=1, metavar=('value'),
                        required=True)
    parser.add_argument("-b", "--baud",
                        help="Serial port to use",
                        nargs=1, metavar=('value'),
                        required=False)
    parser.add_argument("-r", "--reset",
                        help="Reset sequence to use (none, pl2303, mt125.05)",
                        nargs=1, metavar=('value'),
                        required=False)

    opts = parser.parse_args()
    print(opts)

    t = guessImageFormat(opts.file)

    db = chipDb.chipDb()
    c = db.query(t.get_chip_id(),t.get_chip_rev())
    #reset = resetSeqBase.resetSeqBase()
    reset = resetSeqMT12505.resetSeqMT12505('A92XPFQL')

    print("Detected chip:    %s (%s)" % (c.name, c.part))
    if c == None:
        print("ERROR: Failed to auto-detect chip type")
        return 1
    if opts.baud == None:
        opts.baud = [ c.baudrate]
        print("Guessed Baudrate: %d" % c.baudrate)

    term = terminal.terminal(opts.port[0], opts.baud[0])
    reset.resetToHost()
    term.xmodem_send_stream(opts.file)
    return term.loop()
    
