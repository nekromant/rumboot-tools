
from rumboot.testing.user_interaction import *
from rumboot.testing.core import *
from rumboot.testing.test_desc import *
from rumboot.testing.executor import TestExecutor


class _TestingCLI(UserInteraction):

    def __init__(self, test_registry, test_context):
        self.test_registry = test_registry
        self.test_context = test_context
        self.executor = TestExecutor(test_context, self)

    # UserInteraction
    def request_message(self, text):
        input(f"{text} - Press <ENTER>")

    # UserInteraction
    def request_yes_no(self, text):
        answer = input(f"{text} - (Y/N)?")
        if answer in ["Y", "y"]:
            return True
        if answer in ["N", "n"]:
            return False
        print("Unknown answer, interrpreted as NO")
        return False

    # UserInteraction
    def request_option(self, text, options):
        print(text)
        index = 1
        for opt in options:
            print(f"{index} - {opt}")
            index += 1
        answer = input()
        index = int(answer)
        if index < 1 or index > len(options):
            print("Unknown answer, interrpreted as 1")
            return 0
        return index - 1

    def execute(self):
        update_suitable(self.test_registry, self.test_context)
        self.stat_all_tests = 0
        self.stat_skipped = 0
        self.stat_fault = 0
        self.stat_passed = 0
        self.test_registry.test_iteration(self._execute_one_test)
        print(f"==========")
        print(f"All tests : {self.stat_all_tests}")
        print(f"Skipped   : {self.stat_skipped}")
        print(f"Passed    : {self.stat_passed}")
        print(f"Fault     : {self.stat_fault}")

    def _execute_one_test(self, test_desc):
        print(f"=== Processing {test_desc.full_name} ===")
        self.stat_all_tests += 1
        if not test_desc.suitable:
            self.stat_skipped += 1
            print("The test is not suitable for the environment")
            return
        self.executor.exec_test(test_desc)
        if test_desc.status == TEST_STATUS_PASSED:
            self.stat_passed += 1
        elif test_desc.status == TEST_STATUS_FAULT:
            self.stat_fault += 1
        else:
            raise Exception("Unknown test status")


def start_testing_cli(test_registry, test_context):
    test_cli = _TestingCLI(test_registry, test_context)
    test_cli.execute()
