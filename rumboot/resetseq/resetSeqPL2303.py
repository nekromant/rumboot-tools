import os
import time
import usb.core
import usb.util
from parse import parse
from rumboot.resetseq.resetSeqBase import base

class pl2303(base):
    name = "pl2303"
    invert = None
    pl2303_usb_dev = None


    class gpio:
        def __init__(self, dir_reg, dir_mask, out_reg, out_mask):
            self.dir_reg = dir_reg
            self.dir_mask = dir_mask
            self.out_reg = out_reg
            self.out_mask = out_mask


    # GPIO0: power
    GPIO_POWER = gpio(0x01, 0x10, 0x01, 0x40)

    # GPIO1: reset
    GPIO_RESET = gpio(0x01, 0x20, 0x01, 0x80)


    class usb_find_class(object):
        def __init__(self, usb_path):
            self.usb_path = usb_path

        def device_usb_path(self, dev):
            result = str(dev.bus) + "-" + str(dev.port_numbers[0])
            for i in range(1, len(dev.port_numbers)):
                result += "." + str(dev.port_numbers[i])
            return result

        def __call__(self, dev):
            return self.device_usb_path(dev) == self.usb_path


    def read_pl2303_reg(self, reg_num):
        buffer = self.pl2303_usb_dev.ctrl_transfer(
            usb.util.build_request_type(usb.util.CTRL_IN, usb.util.CTRL_TYPE_VENDOR, usb.util.CTRL_RECIPIENT_DEVICE),
            0x01,
            reg_num | 0x80,
            0,
            1,
            1000)
        return buffer[0]


    def write_pl2303_reg(self, reg_num, value):
        self.pl2303_usb_dev.ctrl_transfer(
            usb.util.build_request_type(usb.util.CTRL_OUT, usb.util.CTRL_TYPE_VENDOR, usb.util.CTRL_RECIPIENT_DEVICE),
            0x01,
            reg_num,
            value,
            None,
            1000)


    def set_gpio_out(self, gpio, v):
        if self.invert:
            v = not v

        dir_reg_value = self.read_pl2303_reg(gpio.dir_reg)
        dir_reg_value |= gpio.dir_mask
        self.write_pl2303_reg(gpio.dir_reg, dir_reg_value)

        out_reg_value = self.read_pl2303_reg(gpio.out_reg)
        if v:
            out_reg_value |= gpio.out_mask
        else:
            out_reg_value &= ~gpio.out_mask
        self.write_pl2303_reg(gpio.out_reg, out_reg_value)


    def __init__(self, opts):
        self.invert = opts.pl2303_invert

        if opts.pl2303_port: 
            # try to use a specianl port for PL2303
            tty = opts.pl2303_port[0]
        else:
            # if there is not the special port the main port will be used
            tty = opts.port[0]

        # canonze the port name
        tty = os.path.realpath(tty)
        parsed_tty_number = parse("/dev/ttyUSB{}", tty, case_sensitive=True)
        if not parsed_tty_number:
            raise Exception("cannot parse pl2303 port string: " + tty)
        tty = "ttyUSB" + str(parsed_tty_number[0])

        # get USB path for tty (like "1-1.1.3")
        sys_path = os.path.realpath("/sys/bus/usb-serial/devices/" + tty)
        usb_path = sys_path.split("/")[-2].split(":")[0]

        # find the device
        self.pl2303_usb_dev = usb.core.find(custom_match=self.usb_find_class(usb_path), idVendor=0x67b, idProduct=0x2303)
        if not self.pl2303_usb_dev:
            raise Exception("cannot find pl2303 device by usb path: " + usb_path)

        print("pl2303: %s detected at USB path %s" % (tty, usb_path))


    def resetWithCustomFlags(self, flags=[]):
        print("Please, power-cycle board")


    def power(self, on):
        if on:
            self.set_gpio_out(self.GPIO_POWER, 0)
        else:
            self.set_gpio_out(self.GPIO_POWER, 1)


    def resetToHost(self, flags = []):
        self.set_gpio_out(self.GPIO_POWER, 1)
        self.set_gpio_out(self.GPIO_RESET, 1)
        time.sleep(1)
        self.set_gpio_out(self.GPIO_RESET, 0)
        self.set_gpio_out(self.GPIO_POWER, 0)


    def resetToNormal(self, flags = []):
        self.set_gpio_out(self.GPIO_POWER, 1)
        self.set_gpio_out(self.GPIO_RESET, 1)
        time.sleep(1)
        self.set_gpio_out(self.GPIO_RESET, 0)
        self.set_gpio_out(self.GPIO_POWER, 0)


    def add_argparse_options(parser):
        parser.add_argument("-P", "--pl2303-port",
                            help="PL2303 physical port",
                            nargs=1, metavar=('value'),
                            required=False)
        parser.add_argument("--pl2303-invert",
                            help="Invert all pl2303 gpio signals",
                            action='store_true',
                            default = False,
                            required=False)
