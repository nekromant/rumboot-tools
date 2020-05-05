from rumboot.classLoader import classLoader

class ChipDb(classLoader):
    def __getitem__(self, key):
        ret = super().__getitem__(key)
        if ret:
            return ret
        for name, c in self.classes.items():
            if c.chip_id == int(key):
                return c
        return None

    def load(self, path):
        super().load(path)
        for key,value in self.classes.items():
            value.name = key