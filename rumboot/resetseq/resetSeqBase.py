
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
    chip = None

    def __init__(self, terminal, opts):
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

    def set_chip(self, chip):
        self.chip = chip

    def get_options(self):
        return {}

    def add_argparse_options(this, parser):
        for key,opts in this.get_options(this).items():
            parser.add_argument("--" + key,
                    **opts)

# Legacy API wrappers
    def power(self, on):
        self["POWER"] = on

#Reset is assumed active-HIGH (like on chips)
#Power is assumed active-HIGH (like on most DC-DC)
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
