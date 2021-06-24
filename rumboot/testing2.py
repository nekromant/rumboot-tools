import os
import inspect
import fnmatch
import importlib

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


class TestCollection:

    def __init__(self):
        self.tests = {} # { "test_name": TestDesc, "subdir": { ... } }

    def __addTest(self, path, storagePath, testClass, test_params, name):
        if path == []:
            if name in storagePath:
                raise Exception(f"Test {name} already exists")
            storagePath[name] = TestDesc(testClass, test_params, name)
        else:
            if path[0] not in storagePath:
                storagePath[path[0]] = {}
            if not isinstance(storagePath[path[0]], dict):
                raise Exception(f"Test {path[0]} already exists")
            self.__addTest(path[1:], storagePath[path[0]], testClass, test_params, name)

    def addTest(self, path, testClass, test_params, name):
        self.__addTest(path, self.tests, testClass, test_params, name)


__testCollection = TestCollection()
__testRootPath = os.path.abspath(os.path.curdir)


def __registerOneTest(testModulePath, testClass, test_params, name):
    if testClass == None:
        raise Exception("Test class is not defined")
    relPath = os.path.relpath(os.path.normpath(testModulePath), __testRootPath)
    pathStr = os.path.split(relPath)[0]
    path = pathStr.split(os.sep)
    if path == [""]:
        path = []
    __testCollection.addTest(path, testClass, test_params, name)


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


# ???
def __printTestCollection(d):
    for key, value in d.items():
        if isinstance(value, TestDesc):
            print(f"{key} - {vars(value)}")
        else:
            print(f"=== {key}")
            __printTestCollection(value)


def RumbootStartTesting():
    __printTestCollection(__testCollection.tests)
