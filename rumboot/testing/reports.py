import xml.dom.minidom 
import os
from rumboot.testing.test_desc import *


class JUintReport:

    def __init__(self, log_file_path):
        self._log_file_path = log_file_path
        self._tests = 0
        self._failures = 0
        self._root = xml.dom.minidom.Document()
        self._testsuites = self._root.createElement("testsuites")
        self._root.appendChild(self._testsuites)
        self._testsuite = self._root.createElement("testsuite")
        self._testsuite.setAttribute("name", "Testing result") # ???
        self._testsuites.appendChild(self._testsuite)

    def add_test_result(self, test_desc):
        self._tests += 1
        testcase = self._root.createElement("testcase")
        testcase.setAttribute("name", test_desc.full_name)
        if test_desc.status == TEST_STATUS_NOT_EXECUTED:
            skipped = self._root.createElement("skipped")
            skipped.setAttribute("message", "Skipped")
            testcase.appendChild(skipped)
        elif test_desc.status == TEST_STATUS_FAULT:
            self._failures += 1
            failure = self._root.createElement("failure")
            failure.setAttribute("message", "Failed")
            testcase.appendChild(failure)
        if test_desc.status != TEST_STATUS_NOT_EXECUTED:
            std_out = self._root.createElement("system-out")
            text_value = self._root.createTextNode(test_desc.log_text)
            std_out.appendChild(text_value)
            testcase.appendChild(std_out)
        self._testsuite.appendChild(testcase)

    def flush(self):
        self._testsuite.setAttribute("tests", str(self._tests))
        self._testsuite.setAttribute("errors", "0")
        self._testsuite.setAttribute("failures", str(self._failures))

        file_path = os.path.join(self._log_file_path)
        with open(file_path, "w") as file:
            self._root.writexml(file, addindent="  ", newl="\n", encoding="UTF-8")
