from rumboot.images.imageFormatV3   import ImageFormatV3
from rumboot.images.imageFormatBase import ImageFormatBase
import os


class ImageFormatElfV2(ImageFormatV3):
    MAGIC =  0x464c457f
    name = "ELF"

    def check(self):
        if (ImageFormatBase.check(self)):
            print("[W] ELF File detected, appending V3 header")
            self.fd.seek(0, os.SEEK_SET)
            tmp = self.fd.read(self.file_size)
            # Fill in header values
            self.header["magic"] = super().MAGIC
            self.header["version"] = 3
            self.header["flags"] = 0
            self.header["data_length"] = self.file_size
            self.header["chip_id"] = 0
            self.header["bootsource"] = 0            
            self.file_size = self.file_size + self.get_header_length()
            self.write_header()
            self.dump_header()
            self.fd.seek(self.get_header_length(), os.SEEK_SET)
            self.fd.write(tmp)
        #Always return false for V2/V3 plugin to catch up with this
        return False
