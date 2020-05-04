from rumboot.classLoader import classLoader

class LayoutFactory(classLoader):
    def __getitem__(self, key):
        if key in self.classes:
            return self.classes[key]
        return self.classes["basic"]