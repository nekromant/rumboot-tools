from rumboot.testing2 import *


class RumbootHelloWorldTest3(RumbootTestBase):
    pass


register_test(RumbootHelloWorldTest3)
register_test(RumbootHelloWorldTest3, name = "3TestWithName")
register_test(RumbootHelloWorldTest3, test_params = { "key": "value" }, name = "3TestWithParameter")
register_test(RumbootHelloWorldTest3, test_params = [ { "key": "value1" }, { "key": "value2" }, { "key": "value3" } ], name = "3TestsWithParameter")


if __name__ == "__main__":
    rumboot_start_testing()
