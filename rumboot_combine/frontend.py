from rumboot.ImageFormatDb import ImageFormatDb
from rumboot.LayoutFactory import LayoutFactory

import argparse
import rumboot_packimage
import rumboot

class RumbootPackimage:
    """RumbootPackimage image combiner"""
    def __init__(self, opts):
        pass

def cli():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-combine {} - RumBoot Image Merger Tool\n".format(rumboot.__version__) +
                                    rumboot.__copyright__)
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
                        help='''Set alignment pattern of images in bytes or via keyword (SD, physmap, ini)
                        ''')


    opts = parser.parse_args()

    variant = LayoutFactory("rumboot.layouts")[opts.align](opts.output, opts.align)
    print("Using alignment scheme: " + variant.describe())

    for f in opts.input:
        variant.append(f)

    variant.close()
    print("Wrote " + opts.output + " successfully!")

    return 0
