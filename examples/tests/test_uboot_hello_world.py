from rumboot.testing2 import *

class UBootHelloWorldTest(UBootTestBase):
    requested = {
        "chip": {
            "name": "mm7705"
        }
    }

    def run(self):
        super().run()

        return len(self.terminal.shell_cmd("version")) >= 1


RegisterTest(UBootHelloWorldTest)

# standard epilog
if __name__ == "__main__":
    RumbootStartTesting()
