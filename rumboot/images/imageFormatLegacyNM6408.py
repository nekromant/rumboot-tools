from rumboot.images.imageFormatBase import ImageFormatBase
import os


class ImageFormatLegacyNM6408(ImageFormatBase):
    MAGIC =  0x12345678
    name = "NM6408 (Legacy)"
    format = [
        [4, "magic", "0x%x", "Magic"],
        [4, "data_length", "%d", "Data Length"],
    ]

    def __init__(self, inFile):
        super().__init__(inFile)
        self.header_size = 8

    def get_header_length(self):
        return 8

    def dump_header(self, raw=False, format=False):
        valid = super().dump_header(raw, format)
        crc32 = self.read32(-4, os.SEEK_END)
        self.header["data_crc32"] = crc32
        if (crc32 == self.data_crc32):
            hmatch = "Valid"
        else:
            hmatch = "Invalid, expected: 0x{:X}".format(self.data_crc32)
            valid = False
        self.dump_field([4, "data_crc32", "0x%x", "Data CRC32"],  True, hmatch)
        return valid

    def read_header(self):
        offset = 0
        for f in self.format:
            self.header[f[1]] = self.read_element(offset, f[0])
            offset = offset + f[0]

        if self.header['magic'] != self.MAGIC:
            return

        if (self.header["data_length"] == 0):
            self.data_length = self.file_size - self.get_header_length()
        else:
            self.data_length = self.header["data_length"]
            #Only compute data crc32 for a valid header checksum

        self.data_crc32 = self.crc32(self.get_header_length(), self.get_header_length() + self.data_length - 4)
        
             
    def fix_length(self):
        self.header["data_length"] = (self.file_size - self.get_header_length()) & 0xFFFFFF
        self.data_length = self.header["data_length"]
        self.fix_checksums()

    def fix_checksums(self, calc_data = True):
        self.header["data_length"] = self.data_length
        crc32 = self.crc32(self.get_header_length(), self.get_header_length() + self.data_length - 4)
        self.write_header()
        self.write32(-4, crc32, os.SEEK_END)

    def get_chip_id(self):
        return 6

    def get_chip_rev(self):
        return 1

    def wrap(self):
        self.write32(-4, 0, os.SEEK_END)
        super().wrap()
        return True

#   Because somebody fucked up implementing a usual crc32 in bootrom, we have
#   to reinvent the wheel. 
    def crc32(self, from_byte, to_byte=-1):
        crc32_std = super().crc32(from_byte, to_byte)
        self.fd.seek(from_byte, os.SEEK_SET)
        if (to_byte == -1):
            to_byte = self.file_size
        
        polynom = 0x04C11DB7
        crc = 0xffffffff
        pos = from_byte
        while (pos < to_byte):
            data = self.read32(pos)
            pos = pos + 4
            crc = crc ^ data
            for j in range(0, 32):
                if (crc & 0x80000000):
                    crc = crc << 1
                    crc = crc ^ polynom
                else:
                    crc = crc << 1
                crc =  crc & 0xffffffff                     
        crc =  crc ^ 0xffffffff
        return crc
