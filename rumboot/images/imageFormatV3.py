import os
import heatshrink2
from rumboot.images.imageFormatBase import ImageFormatBase

class ImageFormatV3(ImageFormatBase):
    """
    This class works with version 3.0 images. 
    3.0 are backwars compatible with V2

    enum rumboot_header_flags {
        RUMBOOT_FLAG_COMPRESS = (1 << 0), /** Image data is compressed with heatshrink */
        RUMBOOT_FLAG_DATA     = (1 << 1), /** Image file contains only data to be loaded, it shouldn't be executed */
        RUMBOOT_FLAG_RESERVED = (1 << 2), /** Reserved for further usage */ 
        RUMBOOT_FLAG_SMP      = (1 << 3), /** SMP Image. If supported by target CPU cluster, all cores will start execution */
        RUMBOOT_FLAG_DECAPS   = (1 << 4), /** Remove header before executing and move data to the beginning */
        RUMBOOT_FLAG_RELOCATE = (1 << 5), /** Relocate image before execution to the address in relocation field */
        RUMBOOT_FLAG_SYNC     = (1 << 6), /** Wait for the image to finish before exiting */
        RUMBOOT_FLAG_KILL     = (1 << 7), /** Issue a reset to the target CPU before operating */
    };

    struct __attribute__((packed)) rumboot_bootheader {
        uint32_t magic;
        uint8_t  version;
        uint8_t  flags;
        uint8_t  chip_id;
        uint8_t  chip_rev;
        uint32_t data_crc32;
        uint32_t datalen;

        union
        {
          uint64_t  entry_point;
          uint32_t  entry_point32[2];
        };

        uint64_t  relocation;
        uint32_t  target_cpu_cluster;
        uint32_t  encryption_slot;
        uint32_t  certificate_slot;
        uint32_t  priority;
        uint32_t  reserved[2];
        uint32_t  header_crc32;
        const struct rumboot_bootsource *device;
        char     data[];
    };

    """
    name = "RumBootV3"
    MAGIC = 0xb01dface
    VERSION = 3

    flags = ["COMPRESS", "DATA", "SIGN", "SMP", "DECAPS", "RELOC", "SYNC", "KILL"]
    _flags = {}
    format = [
        [4, "magic",             "0x%x", "Magic"],
        [1, "version",           "0x%x", "Header Version"],
        [1, "flags",             "0x%x", "Flags"],
        [1, "chip_id",           "0x%x", "Chip ID"],
        [1, "chip_rev",          "0x%x", "Chip Revision"],
        [4, "data_crc32",        "0x%x", "Data CRC32"],
        [4, "data_length",       "%d",   "Data Length"],
        [8, "entry_point",       "0x%x", "Entry Point"],
        [8, "relocation",        "0x%x", "Relocation Address"],
        [1, "target_cpu",        "0x%x", "Target CPU Cluster"],
        [1, "encryption_slot",   "0x%x", "Encryption Slot"],
        [1, "certificate_slot",  "0x%x", "Cetificate Slot"],
        [1, "priority",          "0x%x", "Priority"],
        [8, "bootarg0",          "0x%x", "Boot Arg 0"],
        [8, "bootarg1",          "0x%x", "Boot Arg 1"],
        [4, "reserved",          "0x%x", ""],
        [4, "header_crc32",      "0x%x", "Header CRC32"],
        [4, "bootsource",        "0x%x", ""],
    ]

    header = {}

    def read_flags(self):
        for k,f in enumerate(self.flags):
            if (self.header["flags"] & (1<<k)):
                self._flags[f] = True
            else:
                self._flags[f] = False

    def write_flags(self):
        the_flags = 0
        for k,f in enumerate(self.flags):
            if self._flags[f]:
                the_flags |= 1<<k
        self.header["flags"]=the_flags
        self.read_flags()

    def serialize_flags(self):
        ret = ""
        total = 0
        for k,f in enumerate(self.flags):
               if self._flags[f]:
                if total>0:
                   ret += " "
                ret += f
                total += 1
        return ret

    def flag(self, flag, value=None):
        if not isinstance(value, bool):
            return self._flags[flag]
        else:
            self._flags[flag] = value
            self.write_flags()

    def relocate(self, address):
        self.flag("RELOC", True)
        self.header["relocation"] = int(address, 16)
        self.write_header()

    def dump_header(self, raw=False, format=False):
        self.read_flags()
        self.hide_field("flags")
        self.hide_field("encryption_slot")
        self.hide_field("certificate_slot")
        if not self.flag("RELOC"):
            self.hide_field("relocation")
        if self.header["priority"] == 0:
            self.hide_field("priority")
        self.hide_field("reserved")
        ret = super().dump_header(raw, format)
        self.dump_field("flags", False, self.serialize_flags(), raw)
        return ret;

    def check(self):
        if (super().check()):
            if self.header["version"] == self.VERSION:
                self.read_flags()
                return True
        return False

    def __init__(self, inFile):
        super().__init__(inFile)

    def wrap(self):
        super().wrap()
        self.header["version"] = 3
        self.write_header()
        return True

    def get_chip_id(self):
        return self.header['chip_id']

    def get_chip_rev(self):
        return self.header['chip_rev']

    def fix_checksums(self, calc_data = True):
       self.write_flags()
       super().fix_checksums(calc_data)

    def compress(self):
        if self.flag("COMPRESS"):
            print("WARN: Image already compressed!")
            return
        uncompressed_length = self.file_size - self.get_header_length()
        self.fd.seek(self.get_header_length(), os.SEEK_SET)
        data = self.fd.read(uncompressed_length)
        data = heatshrink2.compress(data, window_sz2=11, lookahead_sz2=4)
        self.fd.seek(self.get_header_length(), os.SEEK_SET)
        self.fd.truncate(self.get_header_length())
        self.fd.write(data)
        self.flag("COMPRESS", True)
        self.read_file_size()

    def decompress(self):
        if not self.flag("COMPRESS"):
            print("WARN: Image not compressed, can't decompress!")
            return
        compressed_length = self.file_size - self.get_header_length()
        self.fd.seek(self.get_header_length(), os.SEEK_SET)
        data = self.fd.read(compressed_length)
        data = heatshrink2.decompress(data,window_sz2=11, lookahead_sz2=4)
        self.fd.seek(self.get_header_length(), os.SEEK_SET)
        self.fd.truncate(self.get_header_length())
        self.fd.write(data)
        self.flag("COMPRESS", False)
        self.read_file_size()
