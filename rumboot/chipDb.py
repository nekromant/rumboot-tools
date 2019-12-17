from rumboot.classLoader import classLoader

class ChipDb(classLoader):
    def __getitem__(self, key):
        if key in self.classes:
            return self.classes[key]
        for name, c in self.classes.items():
            if c.chip_id == int(key):
                return c
        return None

