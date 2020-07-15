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
import gdbgui.backend
import sys


class ipgdb(threading.Thread):
    gdbcmds = [ ]

    def configure(self, gdb, port, args):
        self.gdb = gdb
        self.port = port
        self.args = args
        target = "target extended-remote 127.0.0.1:" + str(self.port)
        self.add_command("set remotetimeout 10")
        self.add_command(target)

    def add_command(self, cmd):
        self.gdbcmds = self.gdbcmds + [ cmd ]

    def enable_debug(self):
        self.gdbcmds = [ "set debug remote 1" ] + self.gdbcmds

    def gui(self, gui):
        self.gui = gui

    def run(self):
        cmd = self.gdb + " " + self.args
        for c in self.gdbcmds:
            c = c.replace('"','\\"')
            cmd = cmd + " " + "-ex '" + c + "'"
        print("Invoking gdb: " + cmd)
        return os.system(cmd)

class ipgdbgui(ipgdb):
    def run(self):
        sys.argv = [ sys.argv[0] ]
        sys.argv = sys.argv + [ "-g" + self.gdb ]
        arg = "--gdb-args="
        for c in self.gdbcmds:
            arg = arg + "-ex \"" + c + "\" "
        arg = arg + self.args
        sys.argv = sys.argv + [ arg + "" ]            
        print(sys.argv)
        gdbgui.backend.main()


def cli():
    resets  = ResetSeqFactory("rumboot.resetseq")
    formats = ImageFormatDb("rumboot.images")
    chips   = ChipDb("rumboot.chips")

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-gdb {} - Debugger launcher tool\n".format(rumboot.__version__) +
                                    rumboot.__copyright__)
    helper = arghelper();                                
    helper.add_terminal_opts(parser)
    parser.add_argument("-v", "--verbose", 
                        action='store_true',
                        default=False,
                        help="Print serial debug messages during preload phase"),
    parser.add_argument("-z", "--spl-path",
                        help="Path for SPL writers (Debug only)",
                        type=str,
                        required=False)
    parser.add_argument("-L", "--load",
                        help="Load binary on start",
                        action='store_true',
                        default=False,
                        required=False)
    parser.add_argument("-f", "--file",
                        help="Application ELF file to debug",
                        type=str,
                        required=False)
    parser.add_argument("-x", "--exec",
                        help="Execute supplied binary on start (Implies --load)",
                        action='store_true',
                        default=False,
                        required=False)
    parser.add_argument("-R", "--rebuild",
                        help="Attempt to rebuild binary",
                        action='store_true',
                        default=False,
                        required=False)
    parser.add_argument("--debug-remote",
                        help="Send 'set debug remote 1' to gdb for debugging",
                        action='store_true',
                        default=False,
                        required=False)
    parser.add_argument("--debug-serial",
                        help="Send 'set debug serial 1' to gdb for debugging",
                        action='store_true',
                        default=False,
                        required=False)
    parser.add_argument("-g", "--gdb-path",
                        help="Path to flashrom binary",
                        type=str,
                        required=False)
    parser.add_argument("-G", "--gdb-gui",
                        help="Start GDB gui",
                        action='store_true',
                        default=False,
                        required=False)
    parser.add_argument("-c", "--chip_id",
                    help="Chip Id (numeric or name)",
                    required=True)
    parser.add_argument('remaining', nargs=argparse.REMAINDER, default=[], help="Extra gdb arguments (e.g. filename)")


    helper.add_resetseq_options(parser, resets)

    opts = parser.parse_args()
    if opts.remaining and opts.remaining[0] == "--":
        opts.remaining = opts.remaining[1:]
    gdb_args = " ".join(opts.remaining)

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
    
    try:
        spl = c.stub
    except:
        print("ERROR: Target chip (%s) doesn't have a gdb stub" % (c.name))
        return 1

    if opts.spl_path != None:
        spl_path = opts.spl_path
        print("SPL               %s" % (spl_path + c.stub))

    spl = spl_path + c.stub

    if opts.gdb_path:
        gdb = opts.gdb_path
    else:
        gdb = c.gdb

    print(opts.rebuild, opts.file)
    if opts.rebuild and opts.file != None:
        if 0!=os.system("cmake --build . --target " + opts.file):
            os.exit(1)

    print("Reset method:     %s" % (reset.name))
    print("Baudrate:         %d bps" % int(opts.baud[0]))
    print("Port:             %s" % opts.port[0])
    print("GDB:              %s" % gdb)

    if opts.edcl and c.edcl != None:
        term.xfer.selectTransport("edcl")

    reset.resetToHost()
    term.add_binaries(spl)

    term.loop(break_after_uploads=True)
    while True:
        s = term.ser.readline()
        if opts.verbose:
            print(s)
        if s.decode("utf-8", errors="replace").find("STUB READY!") != -1:
            break
    print("gdb-stub is ready for operations, starting gdb..")

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

    if opts.gdb_gui:
        flr = ipgdbgui()
    else:
        flr = ipgdb()

    if opts.debug_remote:
        flr.add_command("set debug remote 1")

    if opts.debug_serial:
        flr.add_command("set debug serial 1")

    if opts.file != None: 
        gdb_args = gdb_args + opts.file

    flr.configure(gdb, port, gdb_args)
    if opts.load or opts.exec:
        flr.add_command("load")

    if opts.exec:
        flr.add_command("continue")

    flr.start()

    #Accept connection
    connection, client_address = server.accept()
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    rd = redirector()
    rd.configure(term.ser, connection)
    rd.start()

    return flr.join()
    



