import os
import inspect
import fnmatch
import importlib
from rumboot.testing.test_desc import *


class TestRegistry:

    def __init__(self):
        self.all_tests = {} # { "test_name": TestDesc, "subdir": { ... } }
        self.test_root_path = os.path.abspath(os.path.curdir)

    def register_tests(self, test_module_path, test_class, params, name):
        if name == None:
            name = test_class.__name__
        if isinstance(params, dict):
            self._register_one_test(test_module_path, test_class, params, name)
        elif isinstance(params, list):
            index = 1
            for p in params:
                self._register_one_test(test_module_path, test_class, p, f"{name}:{index}")
                index += 1
        else:
            raise Exception("Test params must be dict or list")

    def test_iteration(self, func):
        self._test_iteration_recursive(self.all_tests, func)

    def _register_one_test(self, test_module_path, test_class, params, name):
        if test_class == None:
            raise Exception("Test class is not defined")
        relPath = os.path.relpath(os.path.normpath(test_module_path), self.test_root_path)
        pathStr = os.path.split(relPath)[0]
        path = pathStr.split(os.sep)
        if path == [""]:
            path = []
        self._add_test_recursive(path, self.all_tests, test_class, params, name, "")

    def _add_test_recursive(self, path, storage_dict, test_class, params, name, full_name):
        if path == []:
            if name in storage_dict:
                raise Exception(f"Test {name} already exists")
            full_name = full_name + ("." if full_name else "") + name
            storage_dict[name] = TestDesc(test_class, params, name, full_name)
        else:
            if path[0] not in storage_dict:
                storage_dict[path[0]] = {}
            if not isinstance(storage_dict[path[0]], dict):
                raise Exception(f"Test {path[0]} already exists")
            full_name = full_name + ("." if full_name else "") + path[0]
            self._add_test_recursive(path[1:], storage_dict[path[0]], test_class, params, name, full_name)

    def _test_iteration_recursive(self, tests, func):
        for key, value in tests.items():
            if isinstance(value, TestDesc):
                func(value)
            else:
                self._test_iteration_recursive(value, func)


test_registry = TestRegistry()


def rtest(params = {}, name = None):
    test_module_path = os.path.abspath(inspect.stack()[1][1])
    def decorator(test_class):
        test_registry.register_tests(test_module_path, test_class, params, name)
    return decorator


def register_test(test_class, params = {}, name = None):
    test_module_path = os.path.abspath(inspect.stack()[1][1])
    test_registry.register_tests(test_module_path, test_class, params, name)


def rumboot_test_directory(subdirName, filter = "test_*.py"):
    test_module_path = os.path.abspath(inspect.stack()[1][1])
    dir_module_path = os.path.split(test_module_path)[0]
    dir_path = os.path.join(dir_module_path, subdirName)
    for entry in os.scandir(dir_path):
        if entry.is_file and fnmatch.fnmatch(entry.name, filter):
            fullPath = os.path.join(dir_path, os.path.splitext(entry.name)[0])
            relPath = os.path.relpath(fullPath, test_registry.test_root_path)
            moduleName = relPath.replace(os.path.sep, ".")
            importlib.import_module(moduleName)
