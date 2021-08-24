
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
    warned = False
    supported = ["POWER", "RESET"]
    chip = None

    def __init__(self, terminal, opts):
        if opts["port"].find("socket") != -1:
            self.silent = True
        self._states = {}
        self.terminal = terminal

    def __getitem__(self, key):
        if not key in self.supported:
            raise Exception(f"Control {key} in unknown")
        return self._states[key]

    def __setitem__(self, key, value):
        if not key in self.supported:
            raise Exception(f"Control {key} in unknown")
        self._states[key] = value
        
        if self.name == "None" and not self.silent and not self.warned:
            print("Please, power-cycle board...")
            self.warned = True #Show it only once

    def set_chip(self, chip):
        self.chip = chip

    def get_options(self):
        return {}

    def add_argparse_options(self, parser):
        for key,opts in self.get_options(self).items():
            parser.add_argument("--" + key,
                    **opts)

# Legacy API wrappers
    def power(self, on):
        self["POWER"] = on

# Power and reset
# POWER: 1 - active, 0 - offline
# RESET: 1 - active, device is in reset, 0 - normal operation 
    def reset(self):
        self["POWER"] = 0 #Disable power
        self["RESET"] = 1 #Assert reset
        time.sleep(1)
        self["POWER"] = 1 #Enable power
        time.sleep(0.2)
        self["RESET"] = 0 #Remove reset
 
    def resetToHost(self, flags = []):
        self["HOST"] = 1
        self.reset()

    def resetToNormal(self, flags = []):
        self["HOST"] = 0
        self.reset()
