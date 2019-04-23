import sys
import time

#   MT125.05. Shift register on CBUS pins
class resetSeqMT12505:
    name = "MT125.05 (FT232RL)"
    flags = [ ]

    def reg_write_bit(self, bit):
        if bit>0:
            v = 0
        else:
            v = 1
        self.sp.cbus_write(v)    
        self.sp.cbus_write(v | (1<<3))
        self.sp.cbus_write(v)
        self.sp.cbus_write(0)

    def write_reg(self, values):
        self.sp.cbus_write(0)
        i=0
        for v in values:
            i=i+1
            self.reg_write_bit(v)
        self.sp.cbus_write(0)
        self.sp.cbus_write(1<<2)        
        self.sp.cbus_write(0)

    def __init__(self, serial, flags = [0, 0, 0, 0, 0, 0, 0, 0], reset_pin = 5, host_pin = 3):
        import ft232
        self.sp = ft232.Ft232(serial, baudrate=115200)
        self.sp.cbus_setup(mask=0xf, init=0xf)
        self.flags = flags
        self.reset_pin = reset_pin
        self.host_pin = host_pin

    def resetWithCustomFlags(self,flags = [0, 0, 0, 0, 0, 0, 0, 0]):
            tmp = flags
            tmp[self.reset_pin] = 0
            self.write_reg(tmp)
            time.sleep(1)
            tmp[self.reset_pin] = 1
            self.write_reg(tmp)
        
    def resetToHost(self, flags = [0, 0, 0, 0, 0, 0, 0, 0]):
            tmp = self.flags
            tmp[self.host_pin] = 1            
            tmp[self.reset_pin] = 0
            self.write_reg(tmp)
            time.sleep(1)
            tmp[self.reset_pin] = 1
            self.write_reg(tmp)
        
    def resetToNormal(self, flags = [0, 0, 0, 0, 0, 0, 0, 0]):
            tmp = self.flags
            tmp[self.host_pin] = 0            
            tmp[self.reset_pin] = 0
            self.write_reg(tmp)
            time.sleep(1)
            tmp[self.reset_pin] = 1
            self.write_reg(tmp)

