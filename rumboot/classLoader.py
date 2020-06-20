import inspect
import pkgutil

class classLoader():
    iteratable = []

    def __init__(self, objectpath):
        self.opath = objectpath
        self.classes = dict()
        self.load(objectpath)

    def __iter__(self):
        iteratable = []
        for key,value in self.classes.items():
            self.iteratable.append(value)
        return self

    def __next__(self):
        try:
            ret = self.iteratable.pop()
        except:
            raise StopIteration      
        return ret

    def __getitem__(self, key):
        if key in self.classes:
            return self.classes[key]
        for key,value in self.classes.items():
            if type(value).__name__ == key:
                return c            

    def load(self, path):
        p = __import__(path, fromlist=['object'])
        for mod in pkgutil.iter_modules(p.__path__):
            nm = p.__name__ + "." + mod.name
            __import__(nm)

        for name, obj in inspect.getmembers(p):
            if inspect.ismodule(obj):
                p = __import__(obj.__name__, fromlist=['object'])
                for name, cl in inspect.getmembers(p):
                    if inspect.isclass(cl):
                        self.classes[name] = cl
