from parse import *
class base:
    formats = {}        
    def __init__(self, term):
        self.term = term

    def handle_line(self, line):
        for key,value in self.formats.items():
            pres = parse(value, line)
            if pres != None:
                retval = self.action(key, pres)
                if type(retval) is int:
                    return retval
        return False

    #True  - stop processing
    #False - go on processing (not processed)
    #Number - exit code
    def action(self, trigger, result):
        print("base:", self, trigger, result)
        return False
