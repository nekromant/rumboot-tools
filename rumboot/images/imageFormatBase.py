import os
import binascii
import sys

class ImageFormatBase:
    cur_pos = 0
    file_size = 0
    header_size = 64
    data_offset = 68
    endian = "little"
    debug = False
    logger = False;
    tblfmt = "%-24s"
    header_crc32 = 0
    data_crc32   = 0
    data_length  = 0
    MAGIC = -1
    header = {}

    # These field are common and obligatory
    format = [
        [4, "magic", "%x", "Magic"],
        [4, "data_crc32", "0x%x", "Data CRC32"],
        [4, "data_length", "%d", "Data Length"],
        [4, "header_crc32", "0x%x", "Header CRC32"],
    ]

    hidden = {}

    name = "Base"
    def __init__(self, inFile):
        if (type(inFile) is str):
            self.fd = open(inFile, 'r+b')
        else:
            self.fd = inFile
        self.read_file_size()
        self.header_size = 66

    def wrap(self):
        self.fd.seek(0, os.SEEK_SET)
        tmp = self.fd.read(self.file_size)
        self.file_size = self.file_size + self.get_header_length()
        for n,v in enumerate(self.header):
            self.header[v] = 0
        self.header["magic"] = self.MAGIC
        self.write_header()
        self.dump_header()
        self.fd.seek(self.get_header_length(), os.SEEK_SET)
        self.fd.write(tmp)

    def read_file_size(self):
        self.fd.seek(0, os.SEEK_END)
        self.file_size = self.fd.tell()
        self.fd.seek(0, os.SEEK_SET)

    def field_exists(self, name):
        for f in self.format:
            if (f[1] == name):
                return True
        return False

    def hide_field(self, field):
        self.hidden[field] = True

    def dump_field(self, field, format=False, comment=False, raw=False, nocheck=False):

        if (format == False):
            format = self.format

        if(type(field) is list):
            f = field
        else:
            for f in self.format:
                if (f[1]==field):
                    break;

        if raw:
            label = f[1]
        else:
            label = f[3]

        if (comment):
            print((self.tblfmt + f[2] + " [%s]") % (label + ":", self.header[f[1]], comment))
        else:
            print((self.tblfmt + f[2]) % (label + ":", self.header[f[1]]))

    def dump_header(self, raw=False, format=False):
        #Hide fields that need comments from printout
        valid = True
        self.hide_field("header_crc32")
        self.hide_field("data_crc32")
        self.hide_field("data_length")

        if (format == False):
            format = self.format
        print("=== %s Header Information ===" % self.name)
        print((self.tblfmt + "%s") % ("Endianess:", self.endian))
        for f in format:
            show = True
            if (f[1] in self.hidden):
                show = False

            if (show and f[3]):
                self.dump_field(f, raw=raw)

        if (self.header["header_crc32"] == self.header_crc32):
            hmatch = "Valid"
        else:
            hmatch = "Invalid, expected: 0x{:X}".format(self.header_crc32)
            valid = False

        if (hmatch != "Valid"):
            dmatch = "Skipped, invalid header checksum"
        elif (self.header["data_crc32"] == self.data_crc32):
            dmatch = "Valid"
        else:
            dmatch = "Invalid, expected: {:X}".format(self.data_crc32)
            valid = False

        actual = False
        if (self.file_size - self.get_header_length() != self.header["data_length"]):
            actual = "Actual length {}".format(self.file_size - self.get_header_length())

        if (self.field_exists("data_length")):
            self.dump_field("data_length",  False, actual, raw)
        if (self.field_exists("header_crc32")):
            self.dump_field("header_crc32", False, hmatch, raw)
        if (self.field_exists("data_crc32")):
            self.dump_field("data_crc32",   False, dmatch, raw)
        return valid

    def read_header(self):
        offset = 0
        for f in self.format:
            self.header[f[1]] = self.read_element(offset, f[0])
            offset = offset + f[0]
        self.header_crc32 = self.crc32(0, self.get_header_checksum_length())

        if (self.header["data_length"] == 0):
            self.data_length = self.file_size - self.get_header_length()
        else:
            self.data_length = self.header["data_length"]
            #Only compute data crc32 for a valid header checksum
        if (self.header["header_crc32"] == self.header_crc32):
            self.data_crc32 = self.crc32(self.get_header_length(), self.get_header_length() + self.data_length)

    def write_header(self):
        offset = 0
        for f in self.format:
            self.write_element(offset, self.header[f[1]], f[0])
            offset = offset + f[0]

    def fix_length(self):
        self.header["data_length"] = self.file_size - self.get_header_length()
        self.data_length = self.header["data_length"]
        self.fix_checksums()

    def fix_checksums(self, calc_data = True):
        self.header["data_length"] = self.data_length
        if calc_data:
            self.header["data_crc32"] = self.crc32(self.get_header_length(), self.get_header_length() + self.data_length)
        self.write_header()
        self.header["header_crc32"] = self.crc32(0, self.get_header_checksum_length())
        self.write_header()
        self.read_header()

    def get_header_length(self):
        offset = 0
        for f in self.format:
            offset = offset + f[0]
        return offset

    def get_header_checksum_length(self):
        offset = 0
        for f in self.format:
            if (f[1]=="header_crc32"):
                break;
            offset = offset + f[0]
        return offset

    def read_element(self, offset, len, whence = os.SEEK_SET):
        self.fd.seek(offset, whence)
        tmp = self.fd.read(len)
        tmp = int.from_bytes(tmp, self.endian)
        return tmp

    def write_element(self, offset, value, len, whence = os.SEEK_SET):
        self.fd.seek(offset, whence)
        self.fd.write(bytearray(value.to_bytes(len, self.endian)))
        return value

    def read64(self, offset, whence = os.SEEK_SET):
        return self.read_element(offset, 8, whence)

    def read32(self, offset, whence = os.SEEK_SET):
        return self.read_element(offset, 4, whence)

    def read16(self, offset, whence = os.SEEK_SET):
        return self.read_element(offset, 2, whence)

    def read8(self, offset, whence = os.SEEK_SET):
        return self.read_element(offset, 1, whence)

    def write32(self, offset, value, whence = os.SEEK_SET):
        return self.write_element(offset, value, 4, whence)

    def write16(self, offset, value, whence = os.SEEK_SET):
        return self.write_element(offset, value, 2, whence)

    def write8(self, offset, value, whence = os.SEEK_SET):
        return self.write_element(offset, value, 1, whence)

    def crc32(self, from_byte, to_byte=-1):

        self.fd.seek(from_byte, os.SEEK_SET)
        if (to_byte == -1):
            to_byte = self.file_size
        data = self.fd.read(to_byte-from_byte)
        crc32 = (binascii.crc32(data) & 0xffffffff)
        return crc32

    def swap_endian(self):
        if (self.endian == "big"):
                self.endian = "little"
        if (self.endian == "little"):
                self.endian = "big"

    def check(self):
        self.read_header()
        if (self.header["magic"] != self.MAGIC):
            self.endian = "big"
            self.read_header()
            if (self.header["magic"] != self.MAGIC):
                return False
        self.read_header()
        return True

    def set(self, key, value):
        if not key in self.header:
            print("No such key in header: " + key)
        self.header[key] = int(value,16);
        self.write_header()
        self.read_header()

    def get(self, key):
        return self.header[key]

    def add_zeroes(self, count):
        self.fd.seek(0, os.SEEK_END)
        len = int(count)
        self.file_size += len
        while len > 0:
            self.fd.write(bytearray([0]))
            len = len - 1

    def align(self, align):
        self.fd.seek(0, os.SEEK_END)
        align = int(align)
        if not self.file_size % align:
            return
        len = align - (self.file_size % align)
        self.file_size += len 
        while len > 0:
            self.fd.write(bytearray([0]))
            len = len - 1

    def get_chip_id(self):
        return 0

    def get_chip_rev(self):
        return 0