from rumboot_packimage import imageFormatBase
from rumboot_packimage import imageFormatV2
from rumboot_packimage import imageFormatLegacy
from rumboot_packimage import imageFormatElfV2
import argparse
import rumboot_packimage

class RumbootPackimage:
    """RumbootPackimage tool frontend"""
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
                                     description="rumboot-packimage {} - Universal RumBoot Image Manipulation Tool\n".format(rumboot_packimage.__version__) +
                                    "(C) 2018 Andrew Andrianov, RC Module\nhttps://github.com/RC-MODULE")
    parser.add_argument("-f", "--file",
                        help="image file",
                        type=argparse.FileType("r+b"),
                        required=True)
    parser.add_argument("-i", "--info",
                        help="Show information about the image",
                        action="store_true")
    parser.add_argument("-c", "--checksum",
                        help="This option will modify the file! Adds valid length/checksums to the header",
                        action="store_true")
    parser.add_argument("-r", "--raw",
                        help="Display raw header field names",
                        action="store_true")
    parser.add_argument('-g', '--get',
                        nargs=1, metavar=('key'),
                        help='''Get a single field from header. Nothing else will be printed.
                        NOTE: The value will be formatted as hex
                        ''')
    parser.add_argument('-s', '--set',
                        nargs=2, metavar=('key', 'value'),
                        help='''This option will modify the file! Set a header key to specified value.
                                Use -r flag on an existing image to find out what keys exist.
                                Use -c to update the checksums
                        ''')

    opts = parser.parse_args()

    t = guessImageFormat(opts.file);

    if (t == False):
        print("ERROR: Not a valid image, see README.md")
        return 1

    if opts.set != None:
        t.set(opts.set[0], opts.set[1])
        opts.info = True
        print("Setting " + opts.set[0] + " to " + opts.set[1])
        if not opts.checksum:
            print("WARNING: Add -c option to update checksums!")

    if opts.get:
        print("0x%x" % t.get(opts.get[0]))

    if opts.checksum:
        t.fix_checksums()
        print("Wrote valid checksums to image header")
        opts.info = True

    if opts.info:
        t.dump_header(opts.raw)

    return 0
