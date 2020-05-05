from rumboot.chipDb import ChipDb
from rumboot.ImageFormatDb import ImageFormatDb
from rumboot.resetSeq import ResetSeqFactory
from rumboot.cmdline import arghelper
from rumboot.terminal import terminal

import os
import argparse
import rumboot_xflash
import rumboot_packimage
from parse import *
import rumboot
import threading
import socket
from rumboot.server import redirector


class ipflashrom(threading.Thread):
    def configure(self, flashrom, port, args):
        self.flashrom = flashrom
        self.port = port
        self.args = args

    def run(self):
        cmd = self.flashrom + " -p serprog:ip=127.0.0.1:" + str(self.port) + " " + self.args
        #cmd = "nc 127.0.0.1 "+ str(self.port) 
        print("Invoking flashrom: " + cmd)
        return os.system(cmd)


def cli():
    resets  = ResetSeqFactory("rumboot.resetseq")
    formats = ImageFormatDb("rumboot.images")
    chips   = ChipDb("rumboot.chips")

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-flashrom {} - flashrom wrapper tool\n".format(rumboot.__version__) +
                                    rumboot.__copyright__)
    helper = arghelper();                                
    helper.add_terminal_opts(parser)
    parser.add_argument("-v", "--verbose", 
                        action='store_true',
                        default=False,
                        help="Print serial debug messages during preload phase"),
    parser.add_argument("-m", "--memory",
                        help="SPI bus to use. Names match '-m help' of rumboot-xflash",
                        nargs=1, metavar=('memory'),
                        default="help",
                        required=True)                        
    parser.add_argument("-z", "--spl-path",
                        help="Path for SPL writers (Debug only)",
                        type=str,
                        required=False)
    parser.add_argument("-f", "--flashrom-path",
                        help="Path to flashrom binary",
                        type=str,
                        required=False)
    parser.add_argument("-c", "--chip_id",
                    help="Chip Id (numeric or name)",
                    required=True)        
    parser.add_argument('remaining', nargs=argparse.REMAINDER, default=[], help="Flashrom arguments")
#    parser.add_argument('-F', '--flashrom-args', nargs='*', default=[], )

    helper.add_resetseq_options(parser, resets)

    opts = parser.parse_args()
    if opts.remaining and opts.remaining[0] == "--":
        opts.remaining = opts.remaining[1:]
    flashrom_args = " ".join(opts.remaining)

    c = chips[opts.chip_id]
    if (c == None):
        return 1;
 
    helper.detect_terminal_options(opts, c)
    print("Detected chip:    %s (%s)" % (c.name, c.part))

    if c.warning != None:
        print("    --- WARNING ---")
        print(c.warning)        
        print("    --- WARNING ---")
        print("")

    spl_path = os.path.dirname(__file__) + "/tools/"

    if opts.baud == None:
        opts.baud = [ c.baudrate ]

    reset = resets[opts.reset[0]](opts)
    term = terminal(opts.port[0], opts.baud[0])
    term.verbose = opts.verbose
    term.set_chip(c)
    if opts.log:
        term.logstream = opts.log
    
    mem = opts.memory[0]
    if not mem:
        return 1

    if mem == "help":
        for mem,spl in c.flashrom.items():
            print("Memory %16s: %s" % (mem, spl))
        return 1

    try:
        spl = c.flashrom[mem]
    except:
        print("ERROR: Target chip (%s) doesn't have bus '%s'. Run with -m help for a list" % (c.name, mem))
        return 1

    if opts.spl_path != None:
        spl_path = opts.spl_path
        print("SPL               %s" % (spl_path + c.flashrom[mem]))

    spl = spl_path + c.flashrom[mem]

    print("Reset method:     %s" % (reset.name))
    print("Baudrate:         %d bps" % int(opts.baud[0]))
    print("Port:             %s" % opts.port[0])

    flashrom = None

    flashrom_paths = [
        "/usr/local/sbin/flashrom",
        "/sbin/flashrom", 
        "/usr/sbin/flashrom",
        "C:\\flashrom\\flashrom.exe"
        ]

    if opts.flashrom_path and os.path.exists(opts.flashrom_path):
        flashrom = opts.flashrom_path
    elif opts.flashrom_path:
        print("[W] Specified flashrom path (%s) is invalid, trying to guess" % opts.flashrom_path)

    for f in flashrom_paths:
        if os.path.exists(f):
            flashrom = f

    if flashrom == None:
        print("FATAL: Failed to find working flashrom. Please download and install from https://flashrom.org/")
        return 1

    print("FlashRom:         %s" % flashrom)
    print("FlashRom args:    %s" % flashrom_args)

    reset.resetToHost()
    term.add_binaries(spl)

    term.loop(break_after_uploads=True)
    while True:
        s = term.ser.readline()
        if s.decode("utf-8", errors="replace").find("SERPROG READY!") != -1:
            break

    print("Serprog stub ready!")

    if opts.port[0].find("socket://") == -1:
        #Use flashrom directly

        ret = os.system(flashrom + " -p serprog:dev="+opts.port[0] + ":" + opts.baud[0])
        reset.resetToNormal
        return ret


    # If we're here, we'll need to setup socket redirector
    port=20000

    while True:
        try:
            print("Trying port %d" % port)
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(("127.0.0.1", port))
            server.listen()            
            break
        except:
            port = port + 1
            if port > 30000:
                print("Weird shit going on, breaking")
                break

    #Fire up flashrom in background
    flr = ipflashrom()
    flr.configure(flashrom, port, flashrom_args)
    flr.start()

    #Accept connection
    connection, client_address = server.accept()
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    rd = redirector()
    rd.configure(term.ser, connection)
    rd.start()

    return flr.join()
    



