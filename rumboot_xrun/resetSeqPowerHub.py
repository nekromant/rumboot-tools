import os
import time
class resetSeqPowerHub:
    name = "powerhub"
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

class resetSeqPowerHubUsb(resetSeqPowerHub):
    name = "powerhub_usb_0"
    usb_port = 0
    def __init__(self, port):
        self.port = port

    def resetWithCustomFlags(self, flags=[]):
        print("Please, power-cycle board")

    def resetToHost(self, flags = []):
        os.system("powerhubctl port_power_ctl %d 0" % self.usb_port);
        time.sleep(1)
        os.system("powerhubctl port_power_ctl %d 1" % self.usb_port);

    def resetToNormal(self, flags = []):
        os.system("powerhubctl port_power_ctl %d 0" % self.usb_port);
        time.sleep(1)
        os.system("powerhubctl port_power_ctl %d 1" % self.usb_port);

class resetSeqPowerHubUsb1(resetSeqPowerHubUsb):
    name = "powerhub_usb_1"
    usb_port = 1
