from rumboot_packimage import imageFormatBase
from rumboot_packimage import imageFormatV2
from rumboot_packimage import imageFormatLegacy
import argparse
import rumboot_packimage

class RumbootPackimage:
    """RumbootPackimage tool frontend"""
    def __init__(self, opts):
        print("hello")



# --info
# --checksum
# --inject
# --set

def guessImageFormat(file):
    formats = [ imageFormatLegacy.ImageFormatLegacy,
                imageFormatV2.ImageFormatV2
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
    parser.add_argument("-f", "--file", help="image file", type=argparse.FileType("r+b"), required=True)
    parser.add_argument("-i", "--info", help="Show information about the image", action="store_true")
    parser.add_argument("-c", "--checksum", help="Add valid length/checksums to the header", action="store_true")
    opts = parser.parse_args()

    t = guessImageFormat(opts.file);
    if (t == False):
        print("ERROR: Not a valid image, see README.md")
        return 1
    print("Detected %s image, endian: %s" % (t.name, t.endian))


    if opts.checksum:
        t.fix_checksums()
        print("Wrote valid checksums to image header")
        opts.info = True

    if opts.info:
        t.dump_header()
    #t = guessImageFormat("rumboot-basis-Debug-spl-ok.bin");
    #t = guessImageFormat("rumboot-mpw-proto-Debug-iram-ok.bin");

    #t.dump_header()

    #print("Detected %s image, endian: %s" % (t.name, t.endian))
