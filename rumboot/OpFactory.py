from rumboot.classLoader import classLoader
from parse import *

class OpFactory(classLoader):
    objects = dict()
    def __init__(self, objectpath, terminal):
        super().__init__(objectpath)
        for name,cl in self.classes.items():
            self.objects[name] = cl(terminal)

    def handle_line(self, line):
        for name,obj in self.objects.items():
            ret = obj.handle_line(line)
            if type(ret) is int:
                return ret
            if ret == True:
                return ret
        return False
