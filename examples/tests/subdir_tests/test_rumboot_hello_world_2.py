from rumboot.testing.main import rumboot_start_testing
from rumboot.testing.registry import *
from rumboot.testing.base_classes import *


@rtest()
class RumbootHelloWorldTest2(RumbootTestBase):
    timeout = 60

    def run(self):
        return False


@rtest(params = { "key": "value1" }, name = "2TestWithParameter")
class RumbootHelloWorldTest2(RumbootTestBase):
    timeout = 61

    def run(self):
        return False


@rtest(params = [ { "key": "value1" }, { "key": "value2" }, { "key": "value3" } ], name = "2TestWithParameter2")
class RumbootHelloWorldTest2(RumbootTestBase):
    pass


if __name__ == "__main__":
    rumboot_start_testing()
