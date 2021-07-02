from rumboot.testing2 import *
import os


class RumbootTest(RumbootTestBase):

    @classmethod
    def suitable(self, env, test_params):
        if not super(RumbootTest, self).suitable(env, test_params):
            return False
        if test_params["chip_name"] != env["chip"]["name"]:
            return False
        return True

    def run(self):
        super().run()

        self.test_path = os.path.dirname(os.path.realpath(__file__))


        self.test_file = os.path.join(self.env["root_path"], self.test_params["file_path"])
        self.terminal.add_binaries(self.test_file)
        self.terminal.loop(False, True)
        self.terminal.wait("Hello, world!") # ???

        return True


register_test(RumbootTest, test_params = [
    {"chip_name": "mm7705", "file_path": "rumboot-mm7705-Production-legacy-hello.bin"},
    {"chip_name": "oi10", "file_path": "rumboot-oi10-Production-legacy-hello.bin"}
])


# standard epilog
if __name__ == "__main__":
    rumboot_start_testing()
