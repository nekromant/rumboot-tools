import sys
from rumboot.testing.user_interaction import *
from rumboot.testing.core import *
from rumboot.testing.test_desc import *
from rumboot.testing.executor import TestExecutor
from rumboot.testing.reports import JUintReport


class _TestingCLI(UserInteraction):

    def __init__(self, test_registry, test_context):
        self._test_registry = test_registry
        self._test_context = test_context
        self._reports = None
        if self._test_context.env["report_file_path"]:
            self._reports = JUintReport(self._test_context.env["report_file_path"])
        self._executor = TestExecutor(test_context, self)

    # UserInteraction
    def request_message(self, test, text):
        input(f"{test.full_name} - {text} - Press <ENTER>")

    # UserInteraction
    def request_yes_no(self, test, text):
        answer = input(f"{test.full_name} - {text} - (Y/N)?")
        if answer in ["Y", "y"]:
            return True
        if answer in ["N", "n"]:
            return False
        print("Unknown answer, interrpreted as NO")
        return False

    # UserInteraction
    def request_option(self, test, text, options):
        print(f"{test.full_name} - {text}:")
        index = 1
        for opt in options:
            print(f"{index} - {opt}")
            index += 1
        answer = input()
        try:
            index = int(answer)
        except:
            index = 0
        if index < 1 or index > len(options):
            print(f"Unknown answer, interrpreted as {options[0]}")
            return 0
        return index - 1

    def execute(self):
        update_suitable(self._test_registry, self._test_context)
        self._stat_all_tests = 0
        self._stat_skipped = 0
        self._stat_fault = 0
        self._stat_passed = 0
        self._test_registry.test_iteration(self._execute_one_test)
        print(f"==========")
        print(f"All tests : {self._stat_all_tests}")
        print(f"Skipped   : {self._stat_skipped}")
        print(f"Passed    : {self._stat_passed}")
        print(f"Fault     : {self._stat_fault}")
        if self._reports:
            print("Saving reports...")
            self._reports.flush()

    def _execute_one_test(self, test_desc):
        self._stat_all_tests += 1
        self._executor.exec_test(test_desc)
        if test_desc.status == TEST_STATUS_NOT_EXECUTED:
            self._stat_skipped += 1
        elif test_desc.status == TEST_STATUS_PASSED:
            self._stat_passed += 1
        elif test_desc.status == TEST_STATUS_FAULT:
            self._stat_fault += 1
        else:
            raise Exception("Unknown test status")
        if self._reports:
            self._reports.add_test_result(test_desc)


def start_testing_cli(test_registry, test_context):
    test_cli = _TestingCLI(test_registry, test_context)
    test_cli.execute()
