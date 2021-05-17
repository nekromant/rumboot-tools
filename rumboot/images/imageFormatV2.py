from rumboot.images.imageFormatBase import ImageFormatBase

class ImageFormatV2(ImageFormatBase):
    """
    This class works with version 2.0 images.

    struct __attribute__((packed)) rumboot_bootheader {
    uint32_t magic; /* 0xb0ldface */
    uint8_t  version;
    uint8_t  reserved;
    uint8_t  chip_id;
    uint8_t  chip_rev;
    uint32_t data_crc32;
    uint32_t datalen;
    uint32_t entry_point[11];
    uint32_t header_crc32;
    const struct rumboot_bootsource *device;
    char     data[];
};

    """
    name = "RumBootV2"
    MAGIC = 0xb01dface
    VERSION = 2
    format = [
        [4, "magic", "0x%x", "Magic"],
        [1, "version", "0x%x", "Header Version"],
        [1, "reserved", "0x%x", "Reserved"],
        [1, "chip_id", "0x%x", "Chip ID"],
        [1, "chip_rev", "0x%x", "Chip Revision"],
        [4, "data_crc32", "0x%x", "Data CRC32"],
        [4, "data_length", "%d", "Data Length"],
        [4, "entry0",  "0x%x", "Entry Point[0]"],
        [4, "entry1",  "0x%x", "Entry Point[1]"],
        [4, "entry2",  "0x%x", "Entry Point[2]"],
        [4, "entry3",  "0x%x", "Entry Point[3]"],
        [4, "entry4",  "0x%x", "Entry Point[4]"],
        [4, "entry5",  "0x%x", "Entry Point[5]"],
        [4, "entry6",  "0x%x", "Entry Point[6]"],
        [4, "entry7",  "0x%x", "Entry Point[7]"],
        [4, "entry8",  "0x%x", "Entry Point[8]"],
        [4, "entry9",  "0x%x", "Entry Point[9]"],
        [4, "header_crc32", "0x%x", "Header CRC32"],
        [4, "bootsource", "0x%x", ""],
    ]

    header = {}

    def dump_header(self, raw=False, format=False):
        #Hide all unused entry points
        for i in range(1, 10):
            key = "entry" + str(i)
            self.hide_field(key)
        #Dump fields
        return super().dump_header(raw, format)

    def check(self):
        if (super().check()):
            return self.header["version"] == self.VERSION
        return False

    def __init__(self, inFile):
        super().__init__(inFile)
    
    def wrap(self):
        super().wrap()
        self.header["version"] = 2
        self.write_header()
        return True

    def get_chip_id(self):
        return self.header['chip_id']

    def get_chip_rev(self):
        return self.header['chip_rev']
