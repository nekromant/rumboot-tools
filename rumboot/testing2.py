import os
import inspect
import fnmatch
import importlib
import argparse
import yaml
import multiprocessing
import sys

DEFAULT_ENV_FILE_NAME = "env.yaml"

class TestDesc:

    def __init__(self, testClass, test_params, name):
        self.testClass = testClass
        self.test_params = test_params
        self.name = name


class RumbootTestBase:

    def suitable(environment):
        # ??? ToDo
        return True

    def __init__(self, terminal, resetSeq, environment, test_params):
        self.terminal = terminal
        self.resetSeq = resetSeq
        self.environment = environment
        self.test_params = test_params

    def run(self):
        return True


def __addTest(path, storagePath, testClass, test_params, name):
    if path == []:
        if name in storagePath:
            raise Exception(f"Test {name} already exists")
        storagePath[name] = TestDesc(testClass, test_params, name)
    else:
        if path[0] not in storagePath:
            storagePath[path[0]] = {}
        if not isinstance(storagePath[path[0]], dict):
            raise Exception(f"Test {path[0]} already exists")
        __addTest(path[1:], storagePath[path[0]], testClass, test_params, name)


def __registerOneTest(testModulePath, testClass, test_params, name):
    if testClass == None:
        raise Exception("Test class is not defined")
    relPath = os.path.relpath(os.path.normpath(testModulePath), __testRootPath)
    pathStr = os.path.split(relPath)[0]
    path = pathStr.split(os.sep)
    if path == [""]:
        path = []
    __addTest(path, __tests, testClass, test_params, name)


def __registerTests(testModulePath, testClass, test_params, name):
    if name == None:
        name = testClass.__name__

    if isinstance(test_params, dict):
        __registerOneTest(testModulePath, testClass, test_params, name)
    elif isinstance(test_params, list):
        index = 1
        for p in test_params:
            __registerOneTest(testModulePath, testClass, p, f"{name}:{index}")
            index += 1
    else:
        raise Exception("Test params must be dict or list")


def RTest(test_params = {}, name = None):
    testModulePath = os.path.abspath(inspect.stack()[1][1])
    def decorator(testClass):
        __registerTests(testModulePath, testClass, test_params, name)
    return decorator


def RegisterTest(testClass, test_params = {}, name = None):
    testModulePath = os.path.abspath(inspect.stack()[1][1])
    __registerTests(testModulePath, testClass, test_params, name)


def RumbootTestDirectory(subdirName, filter = "test_*.py"):
    testModulePath = os.path.abspath(inspect.stack()[1][1])
    dirModulePath = os.path.split(testModulePath)[0]
    dirPath = os.path.join(dirModulePath, subdirName)
    for entry in os.scandir(dirPath):
        if entry.is_file and fnmatch.fnmatch(entry.name, filter):
            fullPath = os.path.join(dirPath, os.path.splitext(entry.name)[0])
            relPath = os.path.relpath(fullPath, __testRootPath)
            moduleName = relPath.replace(os.path.sep, ".")
            print(moduleName)
            importlib.import_module(moduleName)


def __testIterationRecursive(path, tests, func):
    for key, value in tests.items():
        fullName = path + ("." if path else "") + key
        if isinstance(value, TestDesc):
            func(fullName, value)
        else:
            __testIterationRecursive(fullName, value, func)

def __testIteration(func):
    __testIterationRecursive("", __tests, func)


def __loadEnvironmentFromFile(filePath):
    with open(filePath, 'r') as stream:
        env = yaml.safe_load(stream)
    return env


def __loadEnvironment(opts):
    if opts.env_path != None:
        return __loadEnvironmentFromFile(opts.env_path)
    else:
        if os.path.isfile(DEFAULT_ENV_FILE_NAME):
            return __loadEnvironmentFromFile(DEFAULT_ENV_FILE_NAME)
    return {}


# ???
def __setupEnvironment(env):
    pass


def __testExecution(fullName, desc):
    global __summary_result

    print(f"=== Processing {fullName} ===")
    if not desc.testClass.suitable(__env):
        print("The test is not suitable for the environment")
        return

    terminal = None # ???
    resetSeq = None # ???
    test = desc.testClass(terminal, resetSeq, __env, desc.test_params)

    timeoutSec = 60 # ???
    proc = multiprocessing.Process(target=lambda: sys.exit(0 if test.run() else 1))
    proc.start()
    proc.join(timeout = timeoutSec)

    ext_code = proc.exitcode
    if (ext_code == None):
        proc.terminate()
        proc.join()
        print(f"The test has been terminated by timeout {timeoutSec} seconds")
        result = False
    else:
        result = (ext_code == 0)

    print("Passed" if result else "Fault")
    __summary_result = __summary_result and result


def RumbootStartTesting():
    __setupEnvironment(__env)
    __testIteration(__testExecution)
    print("==========")
    print("All the tests have been passed" if __summary_result else "Some tests have been fault")


__summary_result = True
__tests = {} # { "test_name": TestDesc, "subdir": { ... } }
__testRootPath = os.path.abspath(os.path.curdir)


# starts before test loading
__parser = argparse.ArgumentParser(prog="<rumboot test system>", description="Processing all tests")

__parser.add_argument("-C", "--directory", dest = "root_path", help = "test root directory", default = __testRootPath)
__parser.add_argument("--env", dest = "env_path", help = "environment yaml file", required = False)

__opts = __parser.parse_args()

__env = __loadEnvironment(__opts)
