from rumboot.testing2 import *

@rtest()
class KernelHelloWorldTest(KernelTestBase):

    def run(self):
        super().run()

        return len(self.terminal.shell_cmd("uname -a")) >= 1


# standard epilog
if __name__ == "__main__":
    rumboot_start_testing()
