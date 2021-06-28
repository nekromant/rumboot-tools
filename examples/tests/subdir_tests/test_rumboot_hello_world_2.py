from rumboot.testing2 import *


@RTest()
class RumbootHelloWorldTest2(RumbootTestBase):
    timeout = 60

    def run(self):
        return False


@RTest(test_params = { "key": "value1" }, name = "2TestWithParameter")
class RumbootHelloWorldTest2(RumbootTestBase):
    timeout = 61

    def run(self):
        return False


@RTest(test_params = [ { "key": "value1" }, { "key": "value2" }, { "key": "value3" } ], name = "2TestWithParameter2")
class RumbootHelloWorldTest2(RumbootTestBase):
    pass


if __name__ == "__main__":
    RumbootStartTesting()
