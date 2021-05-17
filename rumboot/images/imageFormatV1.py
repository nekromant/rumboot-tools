from rumboot.images.imageFormatBase import ImageFormatBase

class ImageFormatV1(ImageFormatBase):
    """
    This class works with 1888TX018 (V1) images
    struct bootheader
    {
        uint32_t magic;
        uint32_t length;
        uint32_t entry0;
        uint32_t entry1;
        uint32_t sum;
        uint32_t hdrsum;
        uint8_t imagedata[]; /* Image data. */
    } __attribute__((packed));

    """
    name = "RumBootV1"
    MAGIC = 0xdeadc0de
    format = [
        [4, "magic", "0x%x", "Magic"],
        [4, "data_length", "%d", "Data Length"],
        [4, "entry0",  "0x%x", "Entry Point[0]"],
        [4, "entry1",  "0x%x", "Entry Point[1]"],
        [4, "data_crc32", "0x%x", "Data CRC32"],
        [4, "header_crc32", "0x%x", "Header CRC32"],
    ]

    def __init__(self, inFile):
        super().__init__(inFile)

    def get_chip_id(self):
        return 1

    def get_chip_rev(self):
        return 1 

    def wrap(self):
        return super().wrap()
