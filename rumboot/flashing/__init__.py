import os
import sys
import argparse
import atexit
import threading
import time
import copy
import io
import random
import humanfriendly
import yaml

from parse import *

from rumboot.chipDb import ChipDb
from rumboot.ImageFormatDb import ImageFormatDb
from rumboot.resetSeq import ResetSeqFactory
from rumboot.cmdline import arghelper
from rumboot.terminal import terminal
import rumboot_xrun
import rumboot

from .base import PartitionBase, FlashDeviceBase

from rumboot.chipDb import ChipDb
from rumboot.ImageFormatDb import ImageFormatDb
from rumboot.resetSeq import ResetSeqFactory
from rumboot.cmdline import arghelper
from rumboot.terminal import terminal

import os
import argparse
import rumboot_packimage
from parse import *
import rumboot
from inspect import isclass

from rumboot.classLoader import classLoader

class FlashAlgoFactory(classLoader):
    def __init__(self, path, protocol):
        super().__init__(path)
        self.protocol = protocol

    def __getitem__(self, key):
        for k,v in self.classes.items():
            if issubclass(v,PartitionBase) and issubclass(v,FlashDeviceBase):
                rt = parse(v.device, key)
                if rt and self.protocol == v.protocol:
                    return v

def execute_runlist(term, spl, runlist):
    def prg(total_bytes, position, increment):
        term.progress_update(total_bytes, position, increment)

    for item in runlist:
        partition = item["partition"]
        mem = partition.name
        fl = item['file']

        if item["action"] == "write":
            fl = fl.replace("@SPL", spl)
            fl = open(fl, "rb")
            size = partition.stream_size(fl)
            if size > partition.size:
                print("WARN: File too big and will be truncated")
                size = partition.size

            if not partition.skip_erase_before_write:
                term.progress_start(f"Erasing {mem}", size)
                partition.erase(0, partition.size, callback=prg)
                term.progress_end()

            term.progress_start(f"Writing {mem}", size)
            partition.write(fl, 0, size, callback=prg)
            term.progress_end()
            fl.close()

        if item["action"] == "erase":
            term.progress_start(f"Erasing {mem}", partition.size)
            partition.erase(0, partition.size, callback=prg)
            term.progress_end()

        if item["action"] == "read":
            fl = item["file"]
            fl = open(fl, "wb")
            term.progress_start(f"Reading {mem}", partition.size)
            partition.read(fl, 0, partition.size, callback=prg)
            term.progress_end()
            fl.close()
    


def parse_firmware_file(file, flasher):
    cnf = yaml.load(file, Loader=yaml.FullLoader)
    ret = []
    for name,data in cnf["partitions"].items():
        if type(data["size"]) == str:
            size = humanfriendly.parse_size(data["size"])
        else:
            size = data["size"]            

        fl = None
        offset = None
        if "offset" in data:
            offset =  data["offset"]
        if "file" in data:
            fl =  data["file"]
            action = "write"
        if "action" in data:
            action = data["action"]
        part = flasher.add_partition(name, offset, size)
        item = {
            "partition" : part,
            "action"    : action,
            "file"      : fl
        }
        ret.append(item)

    for key, value in cnf["environment"].items():
        flasher.env(key, value)

    return ret

def rumboot_start_flashing(partmap=None):
    resets  = ResetSeqFactory("rumboot.resetseq")
    formats = ImageFormatDb("rumboot.images")
    chips   = ChipDb("rumboot.chips")

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="rumboot-xflash {} - RumBoot firmware updater tool\n".format(rumboot.__version__) +
                                    rumboot.__copyright__)
    helper = arghelper();                                
    helper.add_file_handling_opts(parser, True)
    helper.add_terminal_opts(parser)
    parser.add_argument("-v", "--verbose", 
                        default=False,
                        action='store_true',
                        help="Print serial debug messages during update"),
    parser.add_argument("-m", "--memory",
                        help="Memory program. Help for a list of memories",
                        metavar=('memory'),
                        default="help")
    parser.add_argument("-z", "--spl-path",
                        help="Path for SPL writers (Debug only)",
                        type=str,
                        required=False)
    parser.add_argument("--no-spl",
                        help="Do not upload spl, assume it boots on it's own (Debug only)",
                        action="store_true",
                        default=False,
                        required=False)
    parser.add_argument("-o", "--offset",
                        help="Memory offset for read/write operations",
                        type=int,
                        default=0,
                        required=False)
    parser.add_argument("-L", "--length",
                        help="How many bytes to read/write (defaults to whole file/flash)",
                        type=int,
                        default=-1,
                        required=False)
    parser.add_argument("-R", "--read",
                        help="Read flash to file",
                        action='store_true',
                        required=False)
    parser.add_argument("-W", "--write",
                        help="Write flash from file",
                        default=False,
                        action='store_true',
                        required=False)
    parser.add_argument("-E", "--erase",
                        help="Erase flash",
                        default=False,
                        action='store_true',
                        required=False)
    parser.add_argument("-F", "--firmware-file",
                        help="Write firmware from configuration file",
                        type=argparse.FileType("r"),
                        default=None,
                        required=False)
    parser.add_argument("-U", "--upload-baudrate",
                        help="Change baudrate for uploads",
                        default=0,
                        type=int,
                        required=False)

    helper.add_resetseq_options(parser, resets)

    opts = parser.parse_args()

    chip = helper.detect_chip_type(opts, chips, formats)
    if not chip:
        return 1

    mem = opts.memory
    if mem == "help":
        print(f"Available memories for chip '{chip.name}'")
        for mem,cfg in chip.memories.items():
            print("%16s: %s" % (mem, cfg["comment"]))
        return 1

    chip, term, reset = helper.create_core_stuff_from_options(opts)

    if opts.read and opts.write:
        print("Please select either --read or --write, not both")
        return 1

    #Open files, rebuild if needed
    #opts.file[0], dumps = helper.process_files(opts.file[0], False)

    spl_path = os.path.dirname(__file__) + "/spl-tools/"

    try:
        config = chip.memories[mem]
        mem = config["device"]
    except:
        print("ERROR: Target chip (%s) doesn't have memory '%s'. Run with -m help for a list" % (chip.name, mem))
        return 1

    if opts.spl_path != None:
        spl_path = opts.spl_path
        print("SPL                              %s" % (spl_path + chip.memories[mem]))

    spl = spl_path + config["spl"]

    term.verbose = opts.verbose
    if not opts.no_spl:
        term.add_binaries(spl)
    if opts.edcl and chip.edcl != None:
        term.xfer.selectTransport("edcl")

    try:
        reset.resetToHost()
    except:
        print("WARN: Reset method doesn't support HOST mode switching")
        print("WARN: If things don't work - check jumpers!")
        reset.reset()
        
    term.loop(break_after_uploads=True)

    flashers = FlashAlgoFactory("rumboot.flashing", config["protocol"])
    flasher = flashers[mem](term, config)
    # ------------------------
    offset = opts.offset
    length = -1

    if "offset" in config:
        offset += config["offset"]
    if "size" in config:
        flasher.size = config["size"]

    flasher.dump()

    if opts.file and len(opts.file) > 1:
        print("ERROR: Only one file may be specified") 
        return 1

    if opts.file and len(opts.file) == 0:
        return 1

    if opts.upload_baudrate == 0 and hasattr(chip, "flashbaudrate"):
         opts.upload_baudrate = chip.flashbaudrate

    if opts.upload_baudrate > 0:
        print(f"WARN: Changing baudrate to {opts.upload_baudrate} bps")
        print( "WARN: If everything freezes - try a different setting via -U / --upload-baudrate")
        flasher.switchbaud(opts.upload_baudrate)

    term.xfer.connect(chip)

    runlist = []
    if opts.firmware_file is None:
        part = flasher.add_partition(mem, opts.offset, opts.length)
        if opts.write:
            action = {
                "partition" : part,
                "action"    : "write",
                "file"      : opts.file[0][0]
            }
            runlist.append(action)

        if opts.read:
            action = {
                "partition" : part,
                "action"    : "read",
                "file"      : opts.file[0][0]
            }
            runlist.append(action)

        if opts.erase:
            action = {
                "partition" : part,
                "action"    : "erase",
                "file"      : None
            }
            runlist.append(action)
    else:
        runlist = parse_firmware_file(opts.firmware_file, flasher)

    execute_runlist(term, spl, runlist)

    if opts.firmware_file or opts.write:
        print("Saving environment and partition information")
        flasher.save_partitions()
        flasher.saveenv()

    return 1

