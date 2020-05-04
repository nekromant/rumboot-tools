from rumboot.ImageFormatDb import ImageFormatDb
from rumboot.LayoutFactory import LayoutFactory

import argparse
import rumboot_packimage

class RumbootPackimage:
    """RumbootPackimage image combiner"""
    def __init__(self, opts):
        print("hello")

def cli():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-combine {} - RumBoot Image Merger Tool\n".format(rumboot_packimage.__version__) +
                                    "(C) 2018 Andrew Andrianov, RC Module\nhttps://github.com/RC-MODULE")
    parser.add_argument("-i", "--input",
                        help="Input image file (may be specified several times)",
                        type=argparse.FileType("r+b"),
                        action="append",
                        required=True)
    parser.add_argument("-o", "--output",
                        help="Output image",
                        required=True)
    parser.add_argument("-a", "--align",
                        default=1,
                        help='''Set alignment of images in bytes. This option also accepts names of the boot sources
                        SD - 512 byte alignment required for SD boot (alias of -a 512)
                        physmap - 8-byte alignment required for physmap boot source (e.g. NOR). (alias of -a 8)
                        ini - Special mode for .ini file appending. Adds a trailing zero and extends the header checksum. Replaces the existing .ini section, if any 
                        ''')


    opts = parser.parse_args()

    variant = LayoutFactory("rumboot.layouts")[opts.align](opts.output, opts.align)
    print("Using alignment scheme: " + variant.describe())

    for f in opts.input:
        variant.append(f)

    variant.close()
    print("Wrote " + opts.output + " successfully!")

    return 0
