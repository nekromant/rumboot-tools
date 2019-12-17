from rumboot.classLoader import classLoader

class ResetSeqFactory(classLoader):
    def __getitem__(self, key):
        if key in self.classes:
            return self.classes[key]
        return self.classes["base"]

    def args(self, parser):
        pass

