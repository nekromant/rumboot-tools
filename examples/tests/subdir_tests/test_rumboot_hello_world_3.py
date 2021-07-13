from rumboot.testing.main import rumboot_start_testing
from rumboot.testing.registry import *
from rumboot.testing.base_classes import *


class RumbootHelloWorldTest3(RumbootTestBase):

    requested = {
        "chip": {
            "name": "never"
        }
    }


register_test(RumbootHelloWorldTest3)
register_test(RumbootHelloWorldTest3, name = "3TestWithName")
register_test(RumbootHelloWorldTest3, params = { "key": "value" }, name = "3TestWithParameter")
register_test(RumbootHelloWorldTest3, params = [ { "key": "value1" }, { "key": "value2" }, { "key": "value3" } ], name = "3TestsWithParameter")


if __name__ == "__main__":
    rumboot_start_testing()
