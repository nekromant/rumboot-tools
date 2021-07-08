from rumboot.testing.main import rumboot_start_testing
from rumboot.testing.registry import *
from rumboot.testing.base_classes import *

@rtest()
class UBootHelloWorldTest(UBootTestBase):
    def run(self):
        super().run()

        return len(self.terminal.shell_cmd("version")) >= 1


# standard epilog
if __name__ == "__main__":
    rumboot_start_testing()
