import argparse
class arghelper:
    def add_file_handling_opts(parser):
        group = parser.add_argument_group('File Handling')
        group.add_argument("-f", "--file",
                        help="image file",
                        type=argparse.FileType("rb"),
                        required=False)
        group.add_argument("-c", "--chip_id",
                        help="Override chip id (by name or chip_id)",
                        nargs=1, metavar=('chip_id'),
                        required=False)        
    
    def add_terminal_opts(parser):
        group = parser.add_argument_group('Serial Terminal Settings')
        group.add_argument("-l", "--log",
                        help="Log terminal output to file",
                        type=argparse.FileType("w+"),
                        required=False)
        group.add_argument("-p", "--port",
                        help="Serial port to use",
                        nargs=1, metavar=('port'),
                        default=["/dev/ttyUSB0"],
                        required=False),
        group.add_argument("-b", "--baud",
                        help="Serial line speed",
                        nargs=1, metavar=('speed'),
                        required=False)

    def add_resetseq_options(parser, rfactory):
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
        

    def detect_chip_type(opts, chips, formats):
        c = None
        try:
            t = formats.guess(opts.file)
            c = chips[t.get_chip_id()]
        except:
            pass

        if opts.chip_id != None:
            c = chips[opts.chip_id[0]]

        if c == None:
            print("ERROR: Failed to auto-detect chip type")
            print("HINT: Specify a file (-f) or set chip id manually (-c)")
        return c

    def set_baudrate_opts():
        pass
