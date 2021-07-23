import os
import argparse
from rumboot.cmdline import arghelper
from rumboot.resetSeq import ResetSeqFactory
from rumboot.chipDb import ChipDb
from rumboot.testing.yaml import *


DEFAULT_ENV_FILE_NAME = "env.yaml"


class TestContext:

    def __init__(self):
        self.opts = None
        self.env = {}
        self.resets = ResetSeqFactory("rumboot.resetseq")
        self.chips = ChipDb("rumboot.chips")
        self.chip = None

    def process_cmdline(self):
        parser = argparse.ArgumentParser(prog="<rumboot test system>", description="Processing all tests")
        parser.add_argument("-C", "--directory", dest = "root_path", help="test root directory", required=False)
        parser.add_argument("--env", dest = "env_path", help="environment yaml file", required=False)
        parser.add_argument("--report", dest = "report_file_path", help="JUnit report file", required=False)
        parser.add_argument("--gui", dest = "gui", help = "start GUI mode", action="store_true", default=False)

        helper = arghelper()
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
        self.env["chip"] = self.env.get("chip", {})
        chip_id_or_name = self.env["chip"].get("name", None)
        if self.opts.chip_id:
            chip_id_or_name = self.opts.chip_id[0]
        self.chip = self.chips[chip_id_or_name]
        if self.chip == None:
            raise Exception("Failed to detect chip type")

        self.env["chip"]["name"] = self.chip.name

        self.env["connection"] = self.env.get("connection", {})
        self.env["connection"]["port"] = self.env["connection"].get("port", None)
        if self.opts.port:
            self.env["connection"]["port"] = self.opts.port[0]
        if not self.env["connection"]["port"]:
            raise Exception("Serial port is not defined")

        self.env["connection"]["baud"] = self.env["connection"].get("baud", self.chip.baudrate)
        if self.opts.baud:
            self.env["connection"]["baud"] = self.opts.baud[0]
        if not self.env["connection"]["baud"]:
            raise Exception("Serial port baudrate is not defined")

        self.env["connection"]["transport"] = self.env["connection"].get("transport", "xmodem")
        if self.opts.edcl:
            self.env["connection"]["transport"] = "edcl"
        self.env["connection"]["force_static_arp"] = self.env["connection"].get("force_static_arp", False)
        if self.opts.force_static_arp:
            self.env["connection"]["force_static_arp"] = True
        self.env["connection"]["edcl_ip"] = self.env["connection"].get("edcl_ip", None)
        if self.opts.edcl_ip:
            self.env["connection"]["edcl_ip"] = self.opts.edcl_ip
        self.env["connection"]["edcl_mac"] = self.env["connection"].get("edcl_mac", None)
        if self.opts.edcl_mac:
            self.env["connection"]["edcl_mac"] = self.opts.edcl_mac
        self.env["connection"]["edcl_timeout"] = self.env["connection"].get("edcl_timeout", None)
        if self.opts.edcl_timeout:
            self.env["connection"]["edcl_timeout"] = self.opts.edcl_timeout

        root_path = self.env.get("root_path")
        if self.opts.root_path:
            root_path = self.opts.root_path
        if not root_path:
            root_path = os.path.curdir
        self.env["root_path"] = os.path.abspath(root_path)

        self.env["report_file_path"] = self.env.get("report_file_path", None)
        if self.opts.report_file_path:
            self.env["report_file_path"] = self.opts.report_file_path
        if self.env["report_file_path"]:
            self.env["report_file_path"] = os.path.abspath(self.env["report_file_path"])

        self.env["gui"] = self.opts.gui

    def make_reports(self):
        pass
