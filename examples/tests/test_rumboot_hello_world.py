# import testing framework classes
from rumboot.testing2 import *


# define test as a class
class RumbootHelloWorldTest(RumbootTestBase):
    pass


# register the tests
RegisterTest(RumbootHelloWorldTest)
RegisterTest(RumbootHelloWorldTest, name = "TestWithName")
RegisterTest(RumbootHelloWorldTest, test_params = { "key": "value" }, name = "TestWithParameter")
RegisterTest(RumbootHelloWorldTest, test_params = [ { "key": "value1" }, { "key": "value2" }, { "key": "value3" } ], name = "TestsWithParameter")


# # test class directories registration (optional)
# RumbootTestDirectory(__file__, "subdir_tests", filter="test_*.py", config = config)


# standard epilog
if __name__ == "__main__":
    RumbootStartTesting()
