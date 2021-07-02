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

DEFAULT_ENV_FILE_NAME = "env.yaml"

class TestDesc:

    def __init__(self, test_class, test_params, name):
        self.test_class = test_class
        self.test_params = test_params
        self.name = name


class RumbootTestBase:
    timeout = 5 * 60
    requested = {} # { "param1": "value1", "param2": "value2", { ... } } is compared with the environment

    def __suitable(req, env):
        for key, value in req.items():
            if not key in env:
                return False
            if isinstance(value, dict):
                if not isinstance(env[key], dict):
                    return False
                return RumbootTestBase.__suitable(value, env[key])
            if value != env[key]:
                return False
        return True

    @classmethod
    def suitable(self, env):
        return RumbootTestBase.__suitable(self.requested, env)

    # ??? temporary -> terminal
    def write_command(self, cmd):
        cmd = cmd.encode() + b"\r"
        self.terminal.ser.write(cmd)

    def __init__(self, terminal, resetSeq, env, test_params):
        self.terminal = terminal
        self.resetSeq = resetSeq
        self.env = env
        self.test_params = test_params

    def run(self):
        self.resetSeq.resetToHost()
        time.sleep(5) # Ethernet PHY negotiation time for EDCL loading (ToDo: move to EDCL part)
        return True


class UBootTestBase(RumbootTestBase):

    @classmethod
    def suitable(self, env):
        if not super(UBootTestBase, self).suitable(env):
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
    def suitable(self, env):
        if not super(KernelTestBase, self).suitable(env):
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


def __add_test(path, storagePath, test_class, test_params, name):
    if path == []:
        if name in storagePath:
            raise Exception(f"Test {name} already exists")
        storagePath[name] = TestDesc(test_class, test_params, name)
    else:
        if path[0] not in storagePath:
            storagePath[path[0]] = {}
        if not isinstance(storagePath[path[0]], dict):
            raise Exception(f"Test {path[0]} already exists")
        __add_test(path[1:], storagePath[path[0]], test_class, test_params, name)


def __register_one_test(testModulePath, test_class, test_params, name):
    if test_class == None:
        raise Exception("Test class is not defined")
    relPath = os.path.relpath(os.path.normpath(testModulePath), __test_root_path)
    pathStr = os.path.split(relPath)[0]
    path = pathStr.split(os.sep)
    if path == [""]:
        path = []
    __add_test(path, __tests, test_class, test_params, name)


def __register_tests(testModulePath, test_class, test_params, name):
    if name == None:
        name = test_class.__name__

    if isinstance(test_params, dict):
        __register_one_test(testModulePath, test_class, test_params, name)
    elif isinstance(test_params, list):
        index = 1
        for p in test_params:
            __register_one_test(testModulePath, test_class, p, f"{name}:{index}")
            index += 1
    else:
        raise Exception("Test params must be dict or list")


def RTest(test_params = {}, name = None):
    testModulePath = os.path.abspath(inspect.stack()[1][1])
    def decorator(test_class):
        __register_tests(testModulePath, test_class, test_params, name)
    return decorator


def RegisterTest(test_class, test_params = {}, name = None):
    testModulePath = os.path.abspath(inspect.stack()[1][1])
    __register_tests(testModulePath, test_class, test_params, name)


def RumbootTestDirectory(subdirName, filter = "test_*.py"):
    testModulePath = os.path.abspath(inspect.stack()[1][1])
    dirModulePath = os.path.split(testModulePath)[0]
    dirPath = os.path.join(dirModulePath, subdirName)
    for entry in os.scandir(dirPath):
        if entry.is_file and fnmatch.fnmatch(entry.name, filter):
            fullPath = os.path.join(dirPath, os.path.splitext(entry.name)[0])
            relPath = os.path.relpath(fullPath, __test_root_path)
            moduleName = relPath.replace(os.path.sep, ".")
            importlib.import_module(moduleName)


def __test_iteration_recursive(path, tests, func):
    for key, value in tests.items():
        fullName = path + ("." if path else "") + key
        if isinstance(value, TestDesc):
            func(fullName, value)
        else:
            __test_iteration_recursive(fullName, value, func)


def __test_iteration(func):
    __test_iteration_recursive("", __tests, func)


def __load_environment_from_file(filePath):
    with open(filePath, 'r') as stream:
        env = yaml.safe_load(stream)
    return env


def __load_environment(opts):
    if opts.env_path != None:
        return __load_environment_from_file(opts.env_path)
    else:
        if os.path.isfile(DEFAULT_ENV_FILE_NAME):
            return __load_environment_from_file(DEFAULT_ENV_FILE_NAME)
    return {}


def __fill_runlist(full_name, test_desc):
    __env["runlist"][full_name] = test_desc

# run after test loading
def __setup_environment():
    __env["chip"] = __env.get("chip", {})
    __env["chip"]["name"] = __chip.name

    __env["connection"] = __env.get("connection", {})
    __env["connection"]["port"] = __env["connection"].get("port", None)
    if __opts.port:
        __env["connection"]["port"] = __opts.port[0]
    __env["connection"]["boud"] = __env["connection"].get("boud", __chip.baudrate)
    if __opts.baud:
        __env["connection"]["baud"] = __opts.baud[0]

    __env["connection"]["transport"] = __env["connection"].get("transport", "xmodem")
    if __opts.edcl:
        __env["connection"]["transport"] = "edcl"

    __env["runlist"] = {}
    __test_iteration(__fill_runlist)

    __env["root_path"] = __opts.root_path


def __test_environment():
    if not __env["connection"]["port"]:
        raise Exception("Serial port is not defined")
    if not __env["connection"]["baud"]:
        raise Exception("Serial port baudrate is not defined")


def __test_execution_in_process(desc):
    reset = __resets[__opts.reset[0]](__opts) # ??? opts
    term = terminal(__env["connection"]["port"], __env["connection"]["baud"])
    term.set_chip(__chip)
    term.xfer.selectTransport(__env["connection"]["transport"])
    test = desc.test_class(term, reset, __env, desc.test_params)
    sys.exit(0 if test.run() else 1)


def __test_execution(fullName, desc):
    global __summary_result

    print(f"=== Processing {fullName} ===")
    if not desc.test_class.suitable(__env):
        print("The test is not suitable for the environment")
        return

    timeout_sec = desc.test_class.timeout
    if "timeout" in desc.test_params:
        timeout_sec = desc.test_params["timeout"]

    proc = multiprocessing.Process(target=lambda: __test_execution_in_process(desc))
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
    __summary_result = __summary_result and result


def RumbootStartTesting():
    __setup_environment()
    __test_environment()
    __test_iteration(__test_execution)
    print("==========")
    print("All the tests have been passed" if __summary_result else "Some tests have been fault")


__summary_result = True
__tests = {} # { "test_name": TestDesc, "subdir": { ... } }
__test_root_path = os.path.abspath(os.path.curdir)
__opts = None
__env = None
__resets = None
__formats = None # ??? need
__chips = None
__chip = None


# starts before test loading
__resets  = ResetSeqFactory("rumboot.resetseq")
__formats = ImageFormatDb("rumboot.images") # ???
__chips   = ChipDb("rumboot.chips")

__parser = argparse.ArgumentParser(prog="<rumboot test system>", description="Processing all tests")

__parser.add_argument("-C", "--directory", dest = "root_path", help = "test root directory", default = __test_root_path)
__parser.add_argument("--env", dest = "env_path", help = "environment yaml file", required = False)

__helper = arghelper() # ???
__helper.add_terminal_opts(__parser) # ???
__helper.add_resetseq_options(__parser, __resets) # ???
__helper.add_file_handling_opts(__parser) # ??? file

__opts = __parser.parse_args()

__chip = __helper.detect_chip_type(__opts, __chips, __formats)
if __chip == None:
    raise Exception("Failed to detect chip type")
print("Detected chip: %s (%s)" % (__chip.name, __chip.part))

__env = __load_environment(__opts)
