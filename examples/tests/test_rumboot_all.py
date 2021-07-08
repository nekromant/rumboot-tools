import os
from rumboot.testing.main import rumboot_start_testing
from rumboot.testing.registry import *
from rumboot.testing.base_classes import *


class RumbootTest(RumbootTestBase):

    @classmethod
    def suitable(self, env, params):
        if not super(RumbootTest, self).suitable(env, params):
            return False
        if params["chip_name"] != env["chip"]["name"]:
            return False
        return True

    def run(self):
        super().run()

        self.test_path = os.path.dirname(os.path.realpath(__file__))


        self.test_file = os.path.join(self.env["root_path"], self.params["file_path"])
        self.terminal.add_binaries(self.test_file)
        self.terminal.loop(False, True)
        self.terminal.wait("Hello, world!") # ???

        return True


register_test(RumbootTest, params = [
    {"chip_name": "mm7705", "file_path": "rumboot-mm7705-Production-legacy-hello.bin"},
    {"chip_name": "oi10", "file_path": "rumboot-oi10-Production-legacy-hello.bin"}
])


# standard epilog
if __name__ == "__main__":
    rumboot_start_testing()
