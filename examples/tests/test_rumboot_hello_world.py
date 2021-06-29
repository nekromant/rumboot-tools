# import testing framework classes
from rumboot.testing2 import *

import os


# define test as a class
class RumbootHelloWorldTest(RumbootTestBase):
    timeout = 16
    requested = {
        "chip": {
            "name": "mm7705"
        }
    }

    def run(self):
        super().run()

        self.test_path = os.path.dirname(os.path.realpath(__file__)) # ???
        self.binfile = "rumboot-mm7705-Production-legacy-hello.bin" # ???
        self.test_file = os.path.join(self.test_path, self.binfile) # ???

        self.terminal.add_binaries(self.test_file) # ???
        self.terminal.loop(False, True) # ???
        self.terminal.wait("Hello, world!") # ???

        return True


# register the tests
RegisterTest(RumbootHelloWorldTest)
RegisterTest(RumbootHelloWorldTest, name = "TestWithName")
RegisterTest(RumbootHelloWorldTest, test_params = { "key": "value", "timeout": 180 }, name = "TestWithParameter")
RegisterTest(RumbootHelloWorldTest, test_params = [ { "key": "value1" }, { "key": "value2" }, { "key": "value3" } ], name = "TestsWithParameter")


# # test class directories registration (optional)
RumbootTestDirectory("subdir_tests", filter="test_*.py")


# standard epilog
if __name__ == "__main__":
    RumbootStartTesting()
