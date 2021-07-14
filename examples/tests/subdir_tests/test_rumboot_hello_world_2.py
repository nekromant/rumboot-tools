import time
from rumboot.testing.main import rumboot_start_testing
from rumboot.testing.registry import *
from rumboot.testing.base_classes import *


@rtest()
class RumbootHelloWorldTest2(RumbootTestBase):
    timeout = 10

    def run(self):
        while (True):
            time.sleep(1)
        return False


@rtest()
class RumbootTestUserInteraction(RumbootTestBase):
    timeout = 3600

    def run(self):
        # self.request_message("Вставьте плату А в плату Б")
        # print(self.request_yes_no("Оно вообще работает"))
        # print(self.request_option("Как оно там", ["Все сломалось", "Ничего не работает", "Все пропало"]))
        return True


@rtest(params = { "key": "value1", "description": "Описание теста для тестирования GUI, где много строчек" }, name = "2TestWithParameter")
class RumbootHelloWorldTest2(RumbootTestBase):
    timeout = 60

    def run(self):
        return False


@rtest(params = [ { "key": "value1" }, { "key": "value2" }, { "key": "value3" } ], name = "2TestWithParameter2")
class RumbootHelloWorldTest2(RumbootTestBase):
    pass


if __name__ == "__main__":
    rumboot_start_testing()
