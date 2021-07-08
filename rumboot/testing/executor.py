import sys
import multiprocessing
from rumboot.terminal import terminal
from rumboot.testing.test_desc import *


class TestExecutor:

    def __init__(self, test_context, user_iteraction):
        self.test_context = test_context
        self.user_iteraction = user_iteraction

    def exec_test(self, test_desc):
        timeout_sec = test_desc.test_class.timeout
        if "timeout" in test_desc.params:
            timeout_sec = test_desc.params["timeout"]

        proc = multiprocessing.Process(target=lambda: self._test_execution_in_process(test_desc))
        proc.start()
        proc.join(timeout = timeout_sec)

        ext_code = proc.exitcode
        if (ext_code == None):
            proc.terminate()
            proc.join()
            test_desc.status = TEST_STATUS_FAULT
            print(f"The test has been terminated by timeout {timeout_sec} seconds")
        else:
            if ext_code == 0:
                test_desc.status = TEST_STATUS_PASSED
                print("Passed")
            else:
                test_desc.status = TEST_STATUS_FAULT
                print("Fault")

    def _test_execution_in_process(self, test_desc):
        sys.stdin = open(0) # overwise stdin is devnull for the new process
        reset = self.test_context.resets[self.test_context.opts.reset[0]](self.test_context.opts) # ??? opts
        term = terminal(self.test_context.env["connection"]["port"], self.test_context.env["connection"]["baud"])
        term.set_chip(self.test_context.chip)
        term.xfer.selectTransport(self.test_context.env["connection"]["transport"])
        test = test_desc.test_class(term, reset, self.test_context.env, test_desc.params, self.user_iteraction)
        sys.exit(0 if test.run() else 1)
