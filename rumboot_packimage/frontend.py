from rumboot.ImageFormatDb import ImageFormatDb
import argparse
import rumboot_packimage

class RumbootPackimage:
    """RumbootPackimage tool frontend"""
    def __init__(self, opts):
        print("hello")

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
                        help='''This option will modify the file! Calculates valid checksums to the header.
                        The length is set to cover the full length of file only if it's non-zero. 
                        ''',
                        action="store_true")
    parser.add_argument("-C", "--checksum_fix_length",
                        help="This option will modify the file! The same as --checksum, but always overrides length with the actual length of file",
                        action="store_true")
    parser.add_argument("-r", "--raw",
                        help="Display raw header field names",
                        action="store_true")
    parser.add_argument('-z', '--add_zeroes',
                        nargs=1, metavar=('value'),
                        help='''This option will add N bytes of zeroes to the end of the file (after checksummed area).
                        This is required to avoid propagating 'X' during the next image check during simulation.
                        Normally, you do not need this option
                        ''')
    parser.add_argument('-a', '--align',
                        nargs=1, metavar=('value'),
                        help='''Pad resulting image size to specified alignment
                        ''')
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
    parser.add_argument('-e', '--reverse-endianness',
                        action="store_true",
                        help='''Use this option to reverse endianness of all headers. This will not touch data.
                                For testing only
                        ''')

    opts = parser.parse_args()
    formats = ImageFormatDb("rumboot.images");
    t = formats.guess(opts.file);

    calc_data = True
    if (t == False):
        print("ERROR: Not a valid image, see README.md")
        return 1

    if opts.set != None:
        t.set(opts.set[0], opts.set[1])

        #FixMe: Hack
        if (opts.set[0] == "data_crc32"):
            calc_data = False
        opts.info = True
        print("Setting " + opts.set[0] + " to " + opts.set[1])
        if not opts.checksum:
            print("WARNING: Add -c option to update checksums!")

    if opts.get:
        print("0x%x" % t.get(opts.get[0]))
        return 0

    if opts.reverse_endianness:
        t.swap_endian()

    if (opts.checksum_fix_length):
        t.fix_length()
        opts.info = True
    elif opts.checksum:
        t.fix_checksums(calc_data)
        print("Wrote valid checksums to image header")
        opts.info = True

    if opts.add_zeroes:
        t.add_zeroes(opts.add_zeroes[0])

    if opts.align:
        t.align(opts.align[0])

    if opts.info:
        t.dump_header(opts.raw)

    return 0
