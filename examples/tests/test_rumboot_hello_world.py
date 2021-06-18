# import testing framework classes
from rumboot.testing2 import RumbootTest, RumbootTestDirectory, RumbootGetDefaultConfig, RumbotApplyOverlay, RumbootTestStartAll

# import test base class (does not have to be RumbootTestBase)
from rumboot.testing2 import RumbootTestBase


# define test as a class
class RumbootHelloWorldTest(RumbootTestBase):
    pass


# create configuration (optional)
config = RumbootGetDefaultConfig()


# test class registration
RumbootTest(__file__, RumbootHelloWorldTest, description = "Rumboot Hello World Test", config = config)

# test class directories registration (optional)
RumbootTestDirectory(__file__, "subdir_tests", filter="test_*.py", config = config)


# standard epilog
if __name__ == "__main__":
    RumbootTestStartAll()
