import serial
import time

class redd:
    name = "redd"
    silent = False
    magicsymbol = 'a'
    ser = None
    def __init__(self, opts):
        self.magicsymbol = opts.redd_relay_id
        self.ser = serial.Serial(opts.redd_port)         

    def power(self, on):
        if on:
            self.ser.write(self.magicsymbol.capitalize().encode())
        else:
            self.ser.write(self.magicsymbol.lower().encode())

    def resetWithCustomFlags(self, flags=[]):
        self.power(0)
        time.sleep(1)
        self.power(1)

    def resetToHost(self, flags = []):
        self.power(0)
        time.sleep(1)
        self.power(1)

    def resetToNormal(self, flags = []):
        self.power(0)
        time.sleep(1)
        self.power(1)

    def add_argparse_options(parser):
        parser.add_argument("--redd-port",
                            help="Redd serial port (e.g. /dev/ttyACM1)",
                            default="/dev/ttyACM1",
                            required=False)
        parser.add_argument("--redd-relay-id",
                            help="Redd Relay Id (e.g. A)",
                            default="B",
                            required=False)