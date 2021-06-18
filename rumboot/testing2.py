# ??? from rumboot.chipDb import ChipDb
# ??? from rumboot.ImageFormatDb import ImageFormatDb
# ??? from rumboot.resetSeq import ResetSeqFactory
# ??? from rumboot.cmdline import arghelper
# ??? from rumboot.terminal import terminal
import os
import fnmatch
import importlib
# ??? from typing import Dict, List
# ??? import sys
# ??? import argparse
# ??? import rumboot_xrun
# ??? import rumboot
# ??? from parse import *
# ??? import atexit
# ??? import threading
# ??? import time
# ???
# ???
# ??? # TODO & questions:
# ??? # - Timeout handling in tests
# ??? # - Is atexit a good way to call the actual testing?
# ??? # - Decorator & class instance registration methods
# ??? # - Helper functions to add tests from directory
# ??? # - GUI integration
# ???

def makeClassName(package, className):
    return package + "." + className if package else className

class Test:

    def __init__(self, name, fullName, moduleFileFullPath, testClass, description, config):
        self.name = name                              # RumbootHelloWorldTest ??? may be deleted
        self.fullName = fullName                      # subdir_tests.RumbootHelloWorldTest
        self.moduleFileFullPath = moduleFileFullPath  # /home/user/test/test.py ??? may be deleted
        self.testClass = testClass
        self.description = description
        self.config = config


class TestCollection:

    def __init__(self, name, packageName):
        self.name = name                # subdir_tests ??? may be deleted
        self.packageName = packageName  # tests.subdir_tests ??? may be renamed
        self.tests = []
        self.collections = []


__currentTestCollection = TestCollection("", "")
__rootTestCollection = __currentTestCollection

# ??? really need
class RumbootTestBase:

    def run(self):
        return True


def RumbootGetDefaultConfig():
    config = {}
    #
    # ???
    #
    return config


def RumbotApplyOverlay(config, config_or_yaml):
    #
    # ???
    #
    return config


def RumbootTest(moduleFilePath, testClass, description = "", config = RumbootGetDefaultConfig()):
    test = Test(testClass.__name__, makeClassName(__currentTestCollection.packageName, testClass.__name__), os.path.abspath(moduleFilePath), testClass, description, config)
    __currentTestCollection.tests.append(test)


def RumbootTestDirectory(moduleFilePath, subdirName, filter = "test_*.py", config = RumbootGetDefaultConfig()):
    global __currentTestCollection

    collection = next((x for x in __currentTestCollection.collections if x.name == subdirName), None)
    if collection == None:
        collection = TestCollection(subdirName, makeClassName(__currentTestCollection.packageName, subdirName))
        __currentTestCollection.collections.append(collection)

    saveCurrentCollection = __currentTestCollection
    __currentTestCollection = collection

    dirPath = os.path.join(os.path.dirname(os.path.abspath(moduleFilePath)), subdirName)
    for entry in os.scandir(dirPath):
        if entry.is_file and fnmatch.fnmatch(entry.name, filter):
            moduleName = makeClassName(__currentTestCollection.packageName, os.path.splitext(entry.name)[0])
            importlib.import_module(moduleName)

    __currentTestCollection == saveCurrentCollection


# ???
def __printTestCollection(testCollection):
    print("=== " + testCollection.name)
    for test in testCollection.tests:
        print(vars(test))
    for collection in testCollection.collections:
        __printTestCollection(collection)


def RumbootTestStartAll():
    __printTestCollection(__rootTestCollection)

# ??? class RumbootTestBase(threading.Thread):
# ???     terminal = None
# ???
# ???     def prepare(self, terminal):
# ???         self.terminal = terminal
# ???
# ???     def run(self):
# ???         return self.execute(self.terminal)
# ???
# ???
# ??? class RumbootTestFacility():
# ???     runlist = []
# ???     def __init__(self):
# ???         pass
# ???
# ???     def register(self, test):
# ???         self.runlist.append(test())
# ???
# ???     def run(self, terminal, reset):
# ???         for r in self.runlist:
# ???             reset.resetToHost()
# ???             r.prepare(terminal)
# ???             r.start()
# ???             print("test done", r.join())
# ???
# ???
# ??? __g_facility = RumbootTestFacility()
# ???
# ???
# ??? def RumbootTest(arg):
# ???     print("Registering test", arg)
# ???     __g_facility.register(arg)
# ???
# ???
# ??? def intialize_testing(target_chip=None):
# ???     resets  = ResetSeqFactory("rumboot.resetseq")
# ???     formats = ImageFormatDb("rumboot.images")
# ???     chips   = ChipDb("rumboot.chips")
# ???     c       = chips[target_chip]
# ???
# ???     parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
# ???                                      description="rumboot-factorytest {} - RumBoot Board Testing Framework\n".format(rumboot.__version__) +
# ???                                     rumboot.__copyright__)
# ???     helper = arghelper()
# ???
# ???     helper.add_terminal_opts(parser)
# ???     helper.add_resetseq_options(parser, resets)
# ???
# ???     opts = parser.parse_args()
# ???
# ???     dump_path = os.path.dirname(__file__) + "/romdumps/"
# ???
# ???     helper.detect_terminal_options(opts, c)
# ???
# ???     print("Detected chip:    %s (%s)" % (c.name, c.part))
# ???     if c == None:
# ???         print("ERROR: Failed to auto-detect chip type")
# ???         return 1
# ???     if opts.baud == None:
# ???         opts.baud = [ c.baudrate ]
# ???
# ???     reset = resets[opts.reset[0]](opts)
# ???     term = terminal(opts.port[0], opts.baud[0])
# ???     term.set_chip(c)
# ???
# ???     try:
# ???         romdump = open(dump_path + c.romdump, "r")
# ???         term.add_dumps({'rom' : romdump})
# ???     except:
# ???         pass
# ???
# ???     if opts.log:
# ???         term.logstream = opts.log
# ???
# ???     print("Reset method:               %s" % (reset.name))
# ???     print("Baudrate:                   %d bps" % int(opts.baud[0]))
# ???     print("Port:                       %s" % opts.port[0])
# ???     if opts.edcl and c.edcl != None:
# ???         term.xfer.selectTransport("edcl")
# ???     print("Preferred data transport:   %s" % term.xfer.how)
# ???     print("--- --- --- --- --- --- ")
# ???
# ???     return term, reset
# ???
# ???
# ???
# ??? @atexit.register
# ??? def execute():
# ???     term, reset = intialize_testing("mm7705")
# ???     __g_facility.run(term, reset)
# ???