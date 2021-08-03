import sys
import time
from rumboot.resetseq.resetSeqBase import base
import pygpiotools
import os

#   MT125.05. Shift register on CBUS pins
class mt12505(base):
    name = "MT125.05 (FT232RL)"
    _bits = [0, 0, 0, 0, 0, 0, 0, 0]

    # CB0 : USB_DIN / USB_DOUT
    # CB1 : USB_LOAD
    # CB2 : USB_OE
    # CB3 : USB_CLK 
    # CB4 : LED 

    # Default mapping (from basis)
    # Normally, we should load mapping from per-chip yaml
    mapping = { }

    def __reg_write_bit(self, bit):
        if bit>0:
            v = 0
        else:
            v = 1
        self.sp.cbus_write(v)    
        self.sp.cbus_write(v | (1<<3))
        self.sp.cbus_write(v)
        self.sp.cbus_write(0)

    def __write_reg(self, values):
        import traceback

        self.sp.cbus_write(0)
        for v in reversed(values):
            self.__reg_write_bit(v)
        self.sp.cbus_write(0)
        self.sp.cbus_write(1<<2)
        self.sp.cbus_write(0)

    def __to_mt12505_devices(self, devs):
        ret = []
        for d in devs:
            if d[1].find("MT12505") != -1:
                ret.append(d)
        return ret


    def set_chip(self, chip):
        if hasattr(chip, "mt12505"):
            self._bits = chip.mt12505["default"]
            self.mapping = chip.mt12505["mapping"]
            self.supported = []
            for k,v in self.mapping.items():
                self.supported.append(k)
            print(f"MT12505: Loaded mapping for '{chip.name}'. Defaults: {chip.mt12505['default']}")
            print(f"MT12505: Supported controls: {self.supported}")
        return super().set_chip(chip)

    def __init__(self, terminal, opts):
        # Lazy-init FT232. 
        # On windows systems, if D2XX drivers are not installed
        try:
            import ft232
        except:
            print("ERROR: Failed to load pyft232")
            print("ERROR: Is D2XX/libftdi installed?")
            sys.exit(1)
        # HACK: On some linux systems (debian buster) we can't free libftdi context
        # HACK: or things will segfault
        # HACK: This hack causes intentional memory leak, but prevents segfault
        def dummy(x):
            pass
        try: 
            ft232.libftdi.ftdi.ftdi_free = dummy
        except:
            pass

        serial = opts["mt12505_serial"]
        if opts["mt12505_serial"] == None:
            devices = ft232.list_devices()
            devices = self.__to_mt12505_devices(devices)
            if len(devices) == 0:
                raise Exception("ERROR: No MT12505 devices found") 

            if len(devices) == 1:
                serial = devices[0][0]
            else:
                print("WARNING: Multiple MT12505 devices found, please specify serial")
                for d in devices:
                    print(f"Serial: {d[0]} Description: {d[1]}")
                sys.exit(1)

        self.sp = ft232.Ft232(serial, baudrate=115200)
        self.sp.cbus_setup(mask=0xf, init=0xf)
        return super().__init__(terminal, opts)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        key = self.mapping[key]
        if key >= 0: #Silently ignore dummy items
            self._bits[key] = value
        self.__write_reg(self._bits)

    #No reset/power inversions on these boards
    def reset(self):
        self["RESET"] = 0
        self["POWER"] = 0
        time.sleep(1)
        self["RESET"] = 1
        self["POWER"] = 1

    def get_options(self):
        return {
            "mt12505-serial" : {
                "help"     : "FT232RL serial number to use",
                "default"  : None,
                "required" : False
            }
        }

