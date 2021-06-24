from rumboot.testing2 import *


class RumbootHelloWorldTest3(RumbootTestBase):
    pass


RegisterTest(RumbootHelloWorldTest3)
RegisterTest(RumbootHelloWorldTest3, name = "TestWithName")
RegisterTest(RumbootHelloWorldTest3, test_params = { "key": "value" }, name = "TestWithParameter")
RegisterTest(RumbootHelloWorldTest3, test_params = [ { "key": "value1" }, { "key": "value2" }, { "key": "value3" } ], name = "TestsWithParameter")


if __name__ == "__main__":
    RumbootStartTesting()
