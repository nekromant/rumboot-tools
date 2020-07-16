from rumboot.classLoader import classLoader
from parse import *

class OpFactory(classLoader):
    objects = dict()
    def __init__(self, objectpath, terminal):
        super().__init__(objectpath)
        self.term = terminal
        for name,cl in self.classes.items():
            self.objects[name] = cl(terminal)

    def on_start(self):
        for name,obj in self.objects.items():
            obj.on_start()

    def handle_line(self, line, skipecho):
        for name,obj in self.objects.items():
            ret = obj.handle_line(line)
            if type(ret) is int:
                if not obj.hidden:
                    self.term.log(skipecho, line, end='\n')
                return ret
            if ret == True:
                if not obj.hidden:
                    self.term.log(skipecho, line, end='\n')
                return ret
        self.term.log(skipecho, line, end='\n')
        return False
