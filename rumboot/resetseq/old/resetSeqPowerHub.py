import os
import time
from rumboot.resetseq.resetSeqBase import base

class powerhub(base):
    name = "PowerHub"
    port = 0
    def __init__(self, opts):
        pass

    def power(self, on):
        if on:
            os.system("powerhubctl outlet_power_ctl 0");
        else:
            os.system("powerhubctl outlet_power_ctl 1");


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