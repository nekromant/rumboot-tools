from rumboot.testing2 import *


@RTest()
class RumbootHelloWorldTest2(RumbootTestBase):
    pass


@RTest(test_params = { "key": "value1" }, name = "TestWithParameter")
class RumbootHelloWorldTest2(RumbootTestBase):
    pass


@RTest(test_params = [ { "key": "value1" }, { "key": "value2" }, { "key": "value3" } ], name = "TestWithParameter2")
class RumbootHelloWorldTest2(RumbootTestBase):
    pass


if __name__ == "__main__":
    RumbootStartTesting()
