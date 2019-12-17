import os
import time
from rumboot.resetseq.resetSeqBase import base

class powerhub(base):
    name = "PowerHub"
    def __init__(self, port):
        self.port = port

    def resetWithCustomFlags(self, flags=[]):
        print("Please, power-cycle board")

    def resetToHost(self, flags = []):
        os.system("powerhubctl outlet_power_ctl 0");
        time.sleep(1)
        os.system("powerhubctl outlet_power_ctl 1");

    def resetToNormal(self, flags = []):
        os.system("powerhubctl outlet_power_ctl 0");
        time.sleep(1)
        os.system("powerhubctl outlet_power_ctl 1");