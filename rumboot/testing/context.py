import os
import argparse
from rumboot.cmdline import arghelper
from rumboot.resetSeq import ResetSeqFactory
from rumboot.chipDb import ChipDb
from rumboot.ImageFormatDb import ImageFormatDb # ???
from rumboot.testing.yaml import *


DEFAULT_ENV_FILE_NAME = "env.yaml"


class TestContext:

    def __init__(self):
        self.opts = None
        self.env = {}
        self.resets = ResetSeqFactory("rumboot.resetseq")
        self.formats = ImageFormatDb("rumboot.images") # ??? need
        self.chips = ChipDb("rumboot.chips")
        self.chip = None

    def process_cmdline(self):
        parser = argparse.ArgumentParser(prog="<rumboot test system>", description="Processing all tests")
        parser.add_argument("-C", "--directory", dest = "root_path", help = "test root directory", default = os.path.abspath(os.path.curdir))
        parser.add_argument("--env", dest = "env_path", help = "environment yaml file", required = False)
        parser.add_argument("--gui", dest = "gui", help = "start GUI mode", action="store_true", default = False)

        helper = arghelper() # ???
        helper.add_terminal_opts(parser) # ???
        helper.add_resetseq_options(parser, self.resets) # ???
        helper.add_file_handling_opts(parser) # ??? file

        self.opts = parser.parse_args()

    def load_environment(self):
        self.env = {}
        if self.opts.env_path != None:
            self.env = load_yaml_from_file(self.opts.env_path)
        else:
            if os.path.isfile(DEFAULT_ENV_FILE_NAME):
                self.env = load_yaml_from_file(DEFAULT_ENV_FILE_NAME)

    def setup_environment(self):
        helper = arghelper() # ???
        self.chip = helper.detect_chip_type(self.opts, self.chips, self.formats) # ???
        if self.chip == None:
            raise Exception("Failed to detect chip type")

        self.env["chip"] = self.env.get("chip", {})
        self.env["chip"]["name"] = self.chip.name

        self.env["connection"] = self.env.get("connection", {})
        self.env["connection"]["port"] = self.env["connection"].get("port", None)
        if self.opts.port:
            self.env["connection"]["port"] = self.opts.port[0]
        if not self.env["connection"]["port"]:
            raise Exception("Serial port is not defined")

        self.env["connection"]["boud"] = self.env["connection"].get("boud", self.chip.baudrate)
        if self.opts.baud:
            self.env["connection"]["baud"] = self.opts.baud[0]
        if not self.env["connection"]["baud"]:
            raise Exception("Serial port baudrate is not defined")

        self.env["connection"]["transport"] = self.env["connection"].get("transport", "xmodem")
        if self.opts.edcl:
            self.env["connection"]["transport"] = "edcl"

        self.env["root_path"] = self.opts.root_path
        self.env["gui"] = self.opts.gui
