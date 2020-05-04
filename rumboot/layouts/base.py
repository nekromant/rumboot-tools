import sys
import os
class basic:
    name = "basic"
    align = 1
    fd = None

    def __init__(self, outfile, align = 1):
        align = int(align)
        self.align = align
        self.outfile = outfile
        self.fd = open(outfile, "wb+")

    def append(self, infile):
        opos = self.fd.tell()
        while opos % self.align > 0:
            self.fd.write(b'\00')
            opos = opos + 1
        infile.seek(0, os.SEEK_END)
        size = infile.tell()
        infile.seek(0)
        data = infile.read()
        self.fd.write(data)

    def close(self):
        self.fd.close()

    def describe(self):
        return self.name + "/" + str(self.align) + " bytes"


class physmap(basic):
    name = "physmap"
    def __init__(self, outfile, align):
        super().__init__(outfile, 8)

class SD(basic):
    name = "SD"
    def __init__(self, outfile, align):
        super().__init__(outfile, 512)

class INI(basic):
    name = "ini"
    first = True
    def __init__(self, outfile, align):
        super().__init__(outfile)
    
    def append(self, infile):
        super().append(infile)

        if not first:
            self.fd.write(b'\00')

        first = False

