from rumboot.images.imageFormatBase import ImageFormatBase
import hashlib

class ImageFormatLegacyK1879XB1YA(ImageFormatBase):
    """
    16 bytes starting with 0x77077707 when empty, md5 of 4k of data otherwise
    16 bytes 0x0 when empty, md5 of 4k of data otherwise
    """
    name = "Legacy K1879XB1YA"
    MAGIC = 0x77077707
    format = [
        [16, "magic", "0x%x", "MD5/MAGIC"],
    ]


    def check(self):
        self.read_header()
        #Do we have a magic? 
        if (self.header["magic"] == self.MAGIC):
            self.endian = "little"
            return True
        #Or perhaps we're already signed?
        self.fd.seek(0)
        md5_orig = self.fd.read(16)
        k4 = self.fd.read(4*1024 - 16)
        md5 = hashlib.md5(k4)
        if md5_orig.hex() == md5.hexdigest():
            return True

        return False

    def wrap(self):
        return True

    def fix_checksums(self, calc_data=True):
        self.fd.seek(16)
        k4 = self.fd.read(4*1024 - 16)
        self.fd.seek(0)
        md5 = hashlib.md5(k4)
        self.fd.write(md5.digest())


    def get_chip_id(self):
        return 2

    def get_chip_rev(self):
        return 1    
