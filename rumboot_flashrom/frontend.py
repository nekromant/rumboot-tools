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


def DummyServer():
    def __init__(self):
        pass

    def serve_once(self):
        pass


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
    helper.add_file_handling_opts(parser, True)
    helper.add_terminal_opts(parser)
    parser.add_argument("-v", "--verbose", 
                        action='store_true',
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
    parser.add_argument('-F', '--flashrom-args', nargs='*', help="Flashrom arguments")

    helper.add_resetseq_options(parser, resets)

    opts = parser.parse_args()

    #Open files, rebuild if needed
    opts.file[0], dumps = helper.process_files(opts.file[0], False)

    c = helper.detect_chip_type(opts, chips, formats)
    if (c == None):
        return 1;
 
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
    term.set_chip(c)
    if opts.log:
        term.logstream = opts.log
    
    term.verbose = opts.verbose

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

    flashrom = "/usr/local/sbin/flashrom"

    reset.resetToHost()
    term.add_binaries(spl)
    term.loop(break_after_uploads=True)
    while True:
        s = term.ser.readline()
        print(s)
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
    flr.configure(flashrom, port, "-VVV")
    flr.start()

    #Accept connection
    connection, client_address = server.accept()
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    dummy = DummyServer()

    rd = redirector()
    rd.configure(dummy, term.ser, connection)
    rd.start()

    return flr.join()
    



