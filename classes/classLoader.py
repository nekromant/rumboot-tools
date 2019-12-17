import inspect
import pkgutil

class classLoader():

    def __init__(self, objectpath):
        self.opath = objectpath
        self.classes = dict()
        self.load(objectpath)


    def __getitem__(self, key):
        return self.classes[key]

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
