from rumboot.classLoader import classLoader

class ImageFormatDb(classLoader):
    def guess(self, ifile):
        for n,f in self.classes.items():
            tmp = f(ifile)
            if tmp.check():
                return tmp
        return False

    def wrap(self, ifile, fmt):
        for n,f in self.classes.items():
            if fmt in n:
                tmp = f(ifile)
                if tmp.wrap():
                    return tmp
        return False