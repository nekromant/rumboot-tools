from rumboot.testing import RumbootTest,RumbootTestBase

@RumbootTest
class MyTest(RumbootTestBase):
    name = "MyTest"
    timeout = 10000

    def execute(self, terminal):
        terminal.add_binaries("../build-test/mm7705-PostProduction/rumboot-mm7705-PostProduction-legacy-hello.bin")
        return terminal.loop()

