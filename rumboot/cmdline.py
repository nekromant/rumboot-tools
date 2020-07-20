import argparse
import os
import sys

try:
    import yaml
except:
    yaml = None

class arghelper():
    configs = [
        "~/.rumboot.yaml", 
        "/etc/rumboot.yaml", 
        os.path.dirname(__file__) + "/../rumboot.yaml"
        ]
    config = None
    default_port = "/dev/ttyUSB0"

    def get_default_port(self, chip):
        try:
            ret = self.config['xrun']['chips'][chip.__name__]["port"]
            return ret
        except:
            pass
        
        try: 
            ret = self.config['xrun']['defaults']["port"]
            return ret
        except:
            return self.default_port

    def get_default_baud(self, chip):
        try:
            ret = self.config['xrun']['chips'][chip.name]["baudrate"]
            return ret
        except:
            if chip != None:
                return chip.baudrate
            return 115200

    def __init__(self):
        if yaml == None:
            print("[W] No yaml, disabling config files. Install with 'pip install yaml' to fix")
            return
        for conf in self.configs:
            conf = os.path.expanduser(conf)
            if (os.path.exists(conf)):
                self.load_config(conf)
                break

    def load_config(self, conf):
        print("[!] Using configuration file: " + conf)
        with open(conf, 'r') as stream:
            try:
                self.config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    def process_files(self, files, rebuild):
        ret = files
        dumps = { }
        for k,f in enumerate(files):
            target = f.replace(".bin", ".all")
            dmp = f.replace(".bin", ".dmp")
            if rebuild:
                bres = os.system("cmake --build . --target %s" % target)
                if (bres != 0):
                    sys.exit(bres)

            ret[k] = open(f, "rb")

            try:
                dumps[f] = open(dmp, "r")
            except:
                print("WARN: Missing dump file: " + dmp + ". Detailed traces will be unavailable")
                pass

        return ret, dumps

    def add_file_handling_opts(self, parser, need_file=False):
        group = parser.add_argument_group('File Handling')
        parser.add_argument('-f','--file',action='append',nargs=1,
                        type=str,
                        help="Image file (may be specified multiple times)")
        group.add_argument("-c", "--chip_id",
                        help="Override chip id (by name or chip_id)",
                        nargs=1, metavar=('chip_id'),
                        required=False)            
    def add_terminal_opts(self, parser):
        group = parser.add_argument_group('Connection Settings')
        group.add_argument("-l", "--log",
                        help="Log terminal output to file",
                        type=argparse.FileType("w+"),
                        required=False)
        group.add_argument("-p", "--port",
                        help="Serial port to use",
                        nargs=1, metavar=('port'),
                        required=False),
        group.add_argument("-b", "--baud",
                        help="Serial line speed",
                        type=int,
                        nargs=1, metavar=('speed'),
                        required=False)
        group.add_argument("-e", '--edcl',
                        help="Use edcl for data uploads (when possible)",
                        action="store_true",
                        default=False,
                        required=False)
        group.add_argument('--force-static-arp',
                        help="Always add static ARP entries",
                        action="store_true",
                        default=False,
                        required=False)


    def add_resetseq_options(self, parser, rfactory):
        group = parser.add_argument_group('Reset Sequence options', "These options control how the target board will be reset")
        resetlist = ""
        for r in rfactory.classes:
            resetlist = resetlist + " " + r
        resetlist = resetlist.strip()
        group.add_argument("-r", "--reset",
                        help="Reset sequence to use (%s)" % resetlist,
                        nargs=1, metavar=('method'),
                        default="none",
                        required=False)
        for name, sequence in rfactory.classes.items():
            if hasattr(sequence, "add_argparse_options"):
                g = parser.add_argument_group(name + " reset sequence options")
                sequence.add_argparse_options(g)
        
    def detect_terminal_options(self, opts, chip):
        # Now, let's update default options, if needed
        if opts.port == None:
            opts.port = [ self.get_default_port(chip) ]
        if opts.baud == None:
            opts.baud = [ self.get_default_baud(chip) ]

    def detect_chip_type(self, opts, chips, formats):
        c = None
        try:
            t = formats.guess(opts.file[0][0])
            c = chips[t.get_chip_id()]
        except:
            pass

        if opts.chip_id != None:
            c = chips[opts.chip_id[0]]

        if c == None:
            print("ERROR: Failed to auto-detect chip type")
            print("HINT: Specify a file (-f) or set chip id manually (-c)")

        self.detect_terminal_options(opts, c)
        return c
