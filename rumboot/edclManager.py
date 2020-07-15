from rumboot.edcl import edcl
from rumboot.chipDb import ChipDb
import os
import platform
import arpreq
import netifaces as ni
import time
from netaddr import IPNetwork, IPAddress
class edclmanager(object):
    edcl = None
    verbose = False
    chips = ChipDb("rumboot.chips")
    warned = []
    def __init__(self):
        self.edcl = edcl()

    def check_reachability(self, ip):
        for i in ni.interfaces():
            if not ni.AF_INET in ni.ifaddresses(i):
                continue
            for addr in ni.ifaddresses(i)[ni.AF_INET]:
                if IPAddress(ip) in IPNetwork(addr['addr'] + "/" +addr["netmask"]):
                    return True
        return False

    def buggy_ip(self, params):
        arr = params["ip"].split(".")
        return int(arr[3]) == 0
            
    def __getattribute__(self, key):
        try:
            return object.__getattribute__(self, key)
        except:
            return object.__getattribute__(self.edcl, key)

    def try_connect(self, chip, params):
        if self.buggy_ip(params):
            #FIXME: This logic sucks. 
            #TODO: Implement a better solution to find non-used IP on the subnet
            params["ip"] = params["ip"].replace(".0", ".76")
            self.AddStaticARP(chip, params)
        if not self.check_reachability(params["ip"]) and not params["ip"] in self.warned:
            print("WARNING: IP address %s is not in your subnet." % params["ip"])
            print("WARNING: Please check network interface settings.")
            self.warned.append(params["ip"])
            return None

        if self.verbose:
            print("Testing: %s (%s) IP %s" % (chip.__name__, params["name"], params["ip"]))
        try: 
            ret = self.edcl.connect(params["ip"])
        except:
            return None
        if ret:
            print("Connected: %s (%s)" % (chip.__name__, params["name"]))
            return chip

    def probe(self, chip):
        for params in chip.edcl:
            if None != self.try_connect(chip, params):
                return params
        return None

    def scan(self, match=None):
        ret = []
        if type(match) == int or type(match) == str:
            match = self.chips[match]

        if match == None:
            chips = self.chips
        else:
            chips = { match }
        for c in chips:
            tmp = self.probe(c)
            if tmp != None:
                db = {
                    "chip" : c,
                    "params": tmp
                }
                ret.append(db)
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

    def connect(self, chip, timeout=5):
        start = time.clock_gettime(time.CLOCK_MONOTONIC)
        while start + timeout > time.clock_gettime(time.CLOCK_MONOTONIC):
            ret = self.scan(chip)
            if ret != []:
                return ret
        
