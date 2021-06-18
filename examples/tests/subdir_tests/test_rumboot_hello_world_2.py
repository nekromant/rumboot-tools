from rumboot.testing2 import RumbootTest, RumbootTestStartAll
from rumboot.testing2 import RumbootTestBase


class RumbootHelloWorldTest2(RumbootTestBase):
    pass


RumbootTest(__file__, RumbootHelloWorldTest2)


if __name__ == "__main__":
    RumbootTestStartAll()
