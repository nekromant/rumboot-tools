import subprocess
import os
import platform
import time

import netifaces as ni
from netaddr import IPNetwork, IPAddress
from parse import parse

from rumboot.edcl import edcl
from rumboot.chipDb import ChipDb


class edclmanager(object):
    edcl = None
    verbose = False
    chips = ChipDb("rumboot.chips")
    warned = []
    force_static_arp = False

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
        if self.buggy_ip(params) or self.force_static_arp:
            #FIXME: This logic sucks. 
            #TODO: Implement a better solution to find non-used IP on the subnet
            params["ip"] = params["ip"].replace(".0", ".76")
            self.prepareStaticARP(chip, params)
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

    def showArpWarning(self, cmd):
        print("WARNING: Trying to add ARP record via 'sudo'/'runas'.")
        print("WARNING: If that doesn't work please run manually: %s" % cmd)

    def dropARP(self, chip, params):
        if platform.system() == 'Linux':
            cmd = "sudo arp -d %s" % params["ip"]
        elif platform.system() == 'Windows': 
            cmd = "runas /user:Administrator arp /d %s" % params["ip"]
        else:
            raise("FATAL: Don't know how to add static ARP on %s", platform.system())
        os.system(cmd)
        self.showArpWarning(cmd)

    def addARP(self, chip, params):
        if platform.system() == 'Linux':
            cmd = "sudo arp -s %s %s" % (params["ip"], params["mac"])
        elif platform.system() == 'Windows': 
            cmd = "runas /user:Administrator arp /s %s %s" % (params["ip"], params["mac"].upper().replace(":","-"))
        else:
            raise("FATAL: Don't know how to add static ARP on %s", platform.system())
        os.system(cmd)
        self.showArpWarning(cmd)
        
    def listARP(self):
        ret = {}
        if platform.system() == 'Linux':
            cmd = "/usr/sbin/arp -n"
        elif platform.system() == 'Windows': 
            cmd = "arp -a"
        else:
            raise("FATAL: I don't know how to query ARP on %s", platform.system())
        out = subprocess.Popen(cmd.split(" "), 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE)
        stdout,stderr = out.communicate()
        if platform.system() == 'Linux':
            for l in stdout.decode().split("\n"):
                result = parse("{:<} ether {:>} {:>} {:>}", l)
                if result == None:
                    continue
                ret[result[0]]=result[1]
        elif  platform.system() == 'Windows': 
            for l in stdout.decode().split("\n"):
                result = parse("{:<} {:>} {:>}", l)
                if result == None:
                    continue
                ret[result[0]]=result[1].replace("-",":")
        return ret

    def getARP(self, ip):
        tbl = self.listARP()
        if ip in tbl:
            return tbl[ip]

    def prepareStaticARP(self, chip, params):
        if self.getARP(params["ip"]) and not self.force_static_arp:
            print("Static ARP record already exists, good")
            return
            
        if self.force_static_arp:
            self.dropARP(chip, params)
        self.addARP(chip, params)

    def smartupload(self, address, image, callback = None):
        self.edcl.send_from_file(address + 4, image, callback, 4)
        self.edcl.send_from_file(address    , image, None, 0, 4)

    def connect(self, chip):
        for i in range(3):
            ret = self.scan(chip)
            if ret != []:
                return ret
    