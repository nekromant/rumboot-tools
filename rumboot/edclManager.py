from rumboot.edcl import edcl
from rumboot.chipDb import ChipDb
import os
import platform
import arpreq

class edclmanager(object):
    edcl = None
    verbose = False
    chips = ChipDb("rumboot.chips")
    def __init__(self):
        self.edcl = edcl()

    def __getattribute__(self, key):
        try:
            return object.__getattribute__(self, key)
        except:
            return object.__getattribute__(self.edcl, key)

    def try_connect(self, chip, params):
        if chip.hacks["edclArpBug"]:
            self.AddStaticARP(chip, params)

        if self.verbose:
            print("Testing: %s (%s) IP %s" % (chip.__name__, params["name"], params["ip"]))
        try: 
            self.edcl.connect(params["ip"])
        except:
            return None
        print("Detected: %s (%s)" % (chip.__name__, params["name"]))
        return chip        

    def scan(self, match=None):
        ret = []
        if type(match) == int or type(match) == str:
            match = self.chips[match]

        for c in self.chips:
            if c.edcl != None:
                for params in c.edcl:
                    if None != self.try_connect(c, params):
                        if match == c:
                            self.params = params
                            return c
                        else:
                            ret.append(c)
        return ret

    def test_chip(self, chip):
        pass

    def AddStaticARP(self, chip, params):
        print("WARNING: Chip '%s' has broken EDCL ARP, working around" % chip.__name__)
        if arpreq.arpreq(params["ip"]):
            print("Static ARP record already exists, good")
            return
        if platform.system() == 'Linux':
            cmd = "sudo arp -s %s %s" % (params["ip"], params["mac"])
        elif platform.system() == 'Windows': 
            cmd = "runas /user:Administrator arp /s %s %s" % (params["ip"], params["mac"].upper().replace(":","-"))
        else:
            raise("FATAL: Don't know how to add static ARP on %s", platform.system())
        print("WARNING: Trying to add ARP record via 'sudo'. If that doesn't work")
        print("WARNING: please run manually: %s" % cmd)
        print("WARNING: Sorry for that bug.")
        os.system(cmd)

    def smartupload(self, address, image, callback = None):
        self.edcl.send_from_file(address + 4, image, callback, 4)
        self.edcl.send_from_file(address    , image, None, 0, 4)

    def connect(self, chip):
        return self.scan(chip)
