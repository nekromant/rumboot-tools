import os
import inspect
import fnmatch
import importlib
import argparse
import yaml
import multiprocessing
import sys
import time
from rumboot.resetSeq import ResetSeqFactory
from rumboot.chipDb import ChipDb
from rumboot.ImageFormatDb import ImageFormatDb # ???
from rumboot.cmdline import arghelper # ???
from rumboot.terminal import terminal
from rumboot.testing_gui import start_testing_gui

DEFAULT_ENV_FILE_NAME = "env.yaml"

class TestDesc:

    def __init__(self, test_class, test_params, name):
        self.test_class = test_class
        self.test_params = test_params
        self.name = name


class UserIntercation:

    def request_message(self, text):
        input(f"{text} - Press <ENTER>")

    def request_yes_no(self, text):
        answer = input(f"{text} - (Y/N)?")
        if answer in ["Y", "y"]:
            return True
        if answer in ["N", "n"]:
            return False
        print("Unknown answer, interrpreted as NO")
        return False

    def request_option(self, text, options):
        print(text)
        index = 1
        for opt in options:
            print(f"{index} - {opt}")
            index += 1
        answer = input()
        index = int(answer)
        if index < 1 or index > len(options):
            print("Unknown answer, interrpreted as 1")
            return 0
        return index - 1


class RumbootTestBase:
    timeout = 5 * 60
    requested = {} # { "param1": "value1", "param2": "value2", { ... } } is compared with the environment

    def _suitable(req, env):
        for key, value in req.items():
            if not key in env:
                return False
            if isinstance(value, dict):
                if not isinstance(env[key], dict):
                    return False
                return RumbootTestBase._suitable(value, env[key])
            if value != env[key]:
                return False
        return True

    @classmethod
    def suitable(self, env, test_params):
        return RumbootTestBase._suitable(self.requested, env)

    # ??? temporary -> terminal
    def write_command(self, cmd):
        cmd = cmd.encode() + b"\r"
        self.terminal.ser.write(cmd)

    def __init__(self, terminal, resetSeq, env, test_params, user_interaction):
        self.terminal = terminal
        self.resetSeq = resetSeq
        self.env = env
        self.test_params = test_params
        self.user_interaction = user_interaction

    def run(self):
        self.resetSeq.resetToHost()
        time.sleep(5) # Ethernet PHY negotiation time for EDCL loading (ToDo: move to EDCL part)
        return True


class UBootTestBase(RumbootTestBase):

    @classmethod
    def suitable(self, env, test_params):
        if not super(UBootTestBase, self).suitable(env, test_params):
            return False
        if not "uboot" in env:
            return False
        if not env["uboot"].get("active", False):
            return False
        return True

    def mem_setup(self):
        mem_setup_cmd = self.env["uboot"].get("mem_setup_cmd")
        if mem_setup_cmd != None:
            self.terminal.shell_cmd(mem_setup_cmd)

    def uboot_upload_file(self, addr_as_text, file_path):
        transport = self.env["connection"]["transport"]
        if (transport == "edcl"):
            self.write_command(f"echo UPLOAD to {addr_as_text}. \\\'X\\\' for X-modem, \\\'E\\\' for EDCL")
            self.terminal.add_binaries(file_path)
            self.terminal.loop(False, True)
            self.terminal.wait_prompt()
            self.terminal.ser.write(b"\b") # ??? -> terminal clear E character
# ???         elif (transport == "xmodem"):
# ???             self.hardware.write_command(f"loadx {addr_as_text}")
# ???             self.hardware.load_binaries([file_path])
# ???             self.hardware.wait_shell_prompt()
# ???         else:
# ???             raise "Unsupported transport"

    def run(self):
        super().run()

        binaries = []
        if "spl_path" in self.env["uboot"]:
            binaries.append(os.path.join(self.env["root_path"], self.env["uboot"]["path_base"], self.env["uboot"]["spl_path"]))
        if "uboot_path" in self.env["uboot"]:
            binaries.append(os.path.join(self.env["root_path"], self.env["uboot"]["path_base"], self.env["uboot"]["uboot_path"]))
        for file in binaries:
            self.terminal.add_binaries(file)

        self.terminal.loop(False, True)
        self.terminal.shell_mode("=> ")
        self.terminal.wait_prompt()

        return True


class KernelTestBase(UBootTestBase):

    @classmethod
    def suitable(self, env, test_params):
        if not super(KernelTestBase, self).suitable(env, test_params):
            return False
        if not "kernel" in env:
            return False
        if not env["kernel"].get("active", False):
            return False
        return True

    def run(self):
        super().run()
        self.mem_setup()

        if "bootargs" in self.env["kernel"]:
            self.terminal.shell_cmd(f"setenv bootargs {self.env['kernel']['bootargs']}")

        uimage_path = os.path.join(self.env["root_path"], self.env["kernel"]["path_base"], self.env["kernel"]["uimage_path"])
        self.uboot_upload_file("${loadaddr}", uimage_path)

        dtb_path = os.path.join(self.env["root_path"], self.env["kernel"]["path_base"], self.env["kernel"]["dtb_path"])
        self.uboot_upload_file("${fdt_addr_r}", dtb_path)

        self.write_command("bootm ${loadaddr} - ${fdt_addr_r}")
        self.terminal.wait("{} login:")
        self.write_command(self.env["kernel"]["user"])
        self.terminal.wait("Password:")
        self.write_command(self.env["kernel"]["password"])
        self.terminal.wait("{}#")

        self.write_command('A="=="; PS1="$A> "')
        self.terminal.shell_mode("==> ")
        self.terminal.wait_prompt()

        return True


def _add_test(path, storagePath, test_class, test_params, name):
    if path == []:
        if name in storagePath:
            raise Exception(f"Test {name} already exists")
        storagePath[name] = TestDesc(test_class, test_params, name)
    else:
        if path[0] not in storagePath:
            storagePath[path[0]] = {}
        if not isinstance(storagePath[path[0]], dict):
            raise Exception(f"Test {path[0]} already exists")
        _add_test(path[1:], storagePath[path[0]], test_class, test_params, name)


def _register_one_test(testModulePath, test_class, test_params, name):
    if test_class == None:
        raise Exception("Test class is not defined")
    relPath = os.path.relpath(os.path.normpath(testModulePath), _test_root_path)
    pathStr = os.path.split(relPath)[0]
    path = pathStr.split(os.sep)
    if path == [""]:
        path = []
    _add_test(path, _tests, test_class, test_params, name)


def _register_tests(testModulePath, test_class, test_params, name):
    if name == None:
        name = test_class.__name__

    if isinstance(test_params, dict):
        _register_one_test(testModulePath, test_class, test_params, name)
    elif isinstance(test_params, list):
        index = 1
        for p in test_params:
            _register_one_test(testModulePath, test_class, p, f"{name}:{index}")
            index += 1
    else:
        raise Exception("Test params must be dict or list")


def rtest(test_params = {}, name = None):
    testModulePath = os.path.abspath(inspect.stack()[1][1])
    def decorator(test_class):
        _register_tests(testModulePath, test_class, test_params, name)
    return decorator


def register_test(test_class, test_params = {}, name = None):
    testModulePath = os.path.abspath(inspect.stack()[1][1])
    _register_tests(testModulePath, test_class, test_params, name)


def rumboot_test_directory(subdirName, filter = "test_*.py"):
    testModulePath = os.path.abspath(inspect.stack()[1][1])
    dirModulePath = os.path.split(testModulePath)[0]
    dirPath = os.path.join(dirModulePath, subdirName)
    for entry in os.scandir(dirPath):
        if entry.is_file and fnmatch.fnmatch(entry.name, filter):
            fullPath = os.path.join(dirPath, os.path.splitext(entry.name)[0])
            relPath = os.path.relpath(fullPath, _test_root_path)
            moduleName = relPath.replace(os.path.sep, ".")
            importlib.import_module(moduleName)


def _test_iteration_recursive(path, tests, func):
    for key, value in tests.items():
        fullName = path + ("." if path else "") + key
        if isinstance(value, TestDesc):
            func(fullName, value)
        else:
            _test_iteration_recursive(fullName, value, func)


def _test_iteration(func):
    _test_iteration_recursive("", _tests, func)


def _load_environment_from_file(filePath):
    with open(filePath, 'r') as stream:
        env = yaml.safe_load(stream)
    return env


def _load_environment(opts):
    if opts.env_path != None:
        return _load_environment_from_file(opts.env_path)
    else:
        if os.path.isfile(DEFAULT_ENV_FILE_NAME):
            return _load_environment_from_file(DEFAULT_ENV_FILE_NAME)
    return {}


def _fill_runlist(full_name, test_desc):
    _env["runlist"][full_name] = test_desc

# run after test loading
def _setup_environment():
    _env["chip"] = _env.get("chip", {})
    _env["chip"]["name"] = _chip.name

    _env["connection"] = _env.get("connection", {})
    _env["connection"]["port"] = _env["connection"].get("port", None)
    if _opts.port:
        _env["connection"]["port"] = _opts.port[0]
    _env["connection"]["boud"] = _env["connection"].get("boud", _chip.baudrate)
    if _opts.baud:
        _env["connection"]["baud"] = _opts.baud[0]

    _env["connection"]["transport"] = _env["connection"].get("transport", "xmodem")
    if _opts.edcl:
        _env["connection"]["transport"] = "edcl"

    _env["runlist"] = {}
    _test_iteration(_fill_runlist)

    _env["root_path"] = _opts.root_path
    _env["gui"] = _opts.gui


def _test_environment():
    if not _env["connection"]["port"]:
        raise Exception("Serial port is not defined")
    if not _env["connection"]["baud"]:
        raise Exception("Serial port baudrate is not defined")


def _test_execution_in_process(desc):
    sys.stdin = open(0) # overwise stdin is devnull for the new process
    reset = _resets[_opts.reset[0]](_opts) # ??? opts
    term = terminal(_env["connection"]["port"], _env["connection"]["baud"])
    term.set_chip(_chip)
    term.xfer.selectTransport(_env["connection"]["transport"])
    test = desc.test_class(term, reset, _env, desc.test_params, _user_interaction)
    sys.exit(0 if test.run() else 1)


def _test_execution(fullName, desc):
    global _summary_result

    print(f"=== Processing {fullName} ===")
    if not desc.test_class.suitable(_env, desc.test_params):
        print("The test is not suitable for the environment")
        return

    timeout_sec = desc.test_class.timeout
    if "timeout" in desc.test_params:
        timeout_sec = desc.test_params["timeout"]

    proc = multiprocessing.Process(target=lambda: _test_execution_in_process(desc))
    proc.start()
    proc.join(timeout = timeout_sec)

    ext_code = proc.exitcode
    if (ext_code == None):
        proc.terminate()
        proc.join()
        print(f"The test has been terminated by timeout {timeout_sec} seconds")
        result = False
    else:
        result = (ext_code == 0)

    print("Passed" if result else "Fault")
    _summary_result = _summary_result and result


def rumboot_start_testing():
    _setup_environment()
    _test_environment()

    # ???
    if _env["gui"]:
        start_testing_gui()
    else:
        _test_iteration(_test_execution)
        print("==========")
        print("All the tests have been passed" if _summary_result else "Some tests have been fault")


_summary_result = True
_tests = {} # { "test_name": TestDesc, "subdir": { ... } }
_test_root_path = os.path.abspath(os.path.curdir)
_opts = None
_env = None
_resets = None
_formats = None # ??? need
_chips = None
_chip = None
_user_interaction = None


# starts before test loading
_resets  = ResetSeqFactory("rumboot.resetseq")
_formats = ImageFormatDb("rumboot.images") # ???
_chips   = ChipDb("rumboot.chips")

_parser = argparse.ArgumentParser(prog="<rumboot test system>", description="Processing all tests")

_parser.add_argument("-C", "--directory", dest = "root_path", help = "test root directory", default = _test_root_path)
_parser.add_argument("--env", dest = "env_path", help = "environment yaml file", required = False)
_parser.add_argument("--gui", dest = "gui", help = "start GUI mode", action="store_true", default = False)

_helper = arghelper() # ???
_helper.add_terminal_opts(_parser) # ???
_helper.add_resetseq_options(_parser, _resets) # ???
_helper.add_file_handling_opts(_parser) # ??? file

_opts = _parser.parse_args()

_chip = _helper.detect_chip_type(_opts, _chips, _formats)
if _chip == None:
    raise Exception("Failed to detect chip type")
print("Detected chip: %s (%s)" % (_chip.name, _chip.part))

_user_interaction = UserIntercation()
_env = _load_environment(_opts)
