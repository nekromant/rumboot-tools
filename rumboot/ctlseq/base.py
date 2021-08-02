
#ctlseq["power"] = True
#

class base:
    name = "None"
    silent = False
    def __init__(self, opts):
        if opts.port[0].find("socket") != -1:
            self.silent = True


    # jumpers = {
    #   "host"  : True,
    #   "power" : True,
    # }
    #

    def set_jumpers(self, jumpers : dict):
        pass

    def get_jumpers(self):
        pass

    #Old-style API
    def power(self, on):
        pass

    def resetWithCustomFlags(self, flags=[]):
        pass

    def resetToHost(self, flags = []):
        if not self.silent:
            print("Please, power-cycle board")

    def resetToNormal(self, flags = []):
        pass