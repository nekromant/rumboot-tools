
# _states are:
#    POWER
#    RESET
#    HOST
#    ...

import time
class base:
    name = "None"
    silent = False
    resetdelay = 1
    supported = ["POWER", "RESET"]

    def __init__(self, terminal, opts):
        print(opts)
        if opts["port"].find("socket") != -1:
            self.silent = True
        self._states = {}

    def __getitem__(self, key):
        if not key in self.supported:
            raise Exception(f"Control {key} in unknown")
        return self._states[key]

    def __setitem__(self, key, value):
        if not key in self.supported:
            raise Exception(f"Control {key} in unknown")
        self._states[key] = value
        
        if self.name == "None" and not self.silent:
            print("Please, power-cycle board")


# Legacy API wrappers
    def power(self, on):
        self["POWER"] = on

    def reset(self):
        self["RESET"] = 1
        self["POWER"] = 1
        time.sleep(1)
        self["RESET"] = 0
        self["POWER"] = 0

    def resetToHost(self, flags = []):
        self["HOST"] = 1
        self.reset()

    def resetToNormal(self, flags = []):
        self["HOST"] = 0
        self.reset()

    def get_options(self):
        return {}

    def add_argparse_options(this, parser):
        for key,opts in this.get_options(this).items():
            print(key, opts)
            parser.add_argument("--" + key,
                    **opts)

#print("Hello")
#b = base(None, {"port" : "/dev/ttyUSB0"})
#b.power(1)
#print(b["POWER"])
#print(b._states)