from rumboot.testing2 import RumbootTest, RumbootTestStartAll
from rumboot.testing2 import RumbootTestBase


class RumbootHelloWorldTest3(RumbootTestBase):
    pass


RumbootTest(__file__, RumbootHelloWorldTest3)


if __name__ == "__main__":
    RumbootTestStartAll()
