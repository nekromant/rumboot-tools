from rumboot.classLoader import classLoader

class ImageFormatDb(classLoader):
    def guess(self, ifile):
        for n,f in self.classes.items():
            tmp = f(ifile)
            if tmp.check():
                return tmp
        return False
