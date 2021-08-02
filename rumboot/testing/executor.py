import sys
import io
import threading
import inspect
import ctypes
import time
import traceback
from rumboot.terminal import terminal
from rumboot.testing.test_desc import *


class TestExecutor:

    def __init__(self, test_context, user_interaction, reports=None, log_func=None):
        self._test_context = test_context
        self._user_interaction = user_interaction
        self._reports = reports
        self._log_func = log_func
        self._log_stream = None

    def exec_test(self, test_desc):
        test_desc.status == TEST_STATUS_NOT_EXECUTED
        test_desc.log_text = None

        self._log_stream = io.StringIO()
        self._save_stdout = sys.stdout
        self._save_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        try:
            print(f"=== Processing {test_desc.full_name} ===")
            if test_desc.suitable:
                self._test_execution_with_log(test_desc)
            if test_desc.status == TEST_STATUS_NOT_EXECUTED:
                print("The test is not suitable for the environment")
            elif test_desc.status == TEST_STATUS_PASSED:
                print("Passed")
            elif test_desc.status == TEST_STATUS_FAULT:
                print("Fault")
            else:
                raise Exception("Unknown test status")
        finally:
            sys.stdout = self._save_stdout
            sys.stderr = self._save_stderr
            self._save_stdout = None
            self._save_stderr = None
        test_desc.log_text = self._log_stream.getvalue()
        self._log_stream = None

    # IOBase
    def write(self, text):
        self._log_stream.write(text)
        if self._log_func:
            self._log_func(text)
        else:
            print(text, file=self._save_stdout, end="")

    # IOBase
    def flush(self):
        pass

    def _test_execution_with_log(self, test_desc):
        test_desc.status = TEST_STATUS_FAULT
        timeout_sec = test_desc.test_class.timeout
        if "timeout" in test_desc.params:
            timeout_sec = test_desc.params["timeout"]

        thread = threading.Thread(target=self._test_execution_in_thread, args=[test_desc])
        thread.wait_user = False
        thread.start()
        time_left = timeout_sec
        while time_left > 0:
            thread.join(timeout=1)
            if not thread.is_alive():
                break
            if not thread.wait_user:
                time_left -= 1

        if thread.is_alive():
            while thread.is_alive():
                _async_raise(thread.ident, SystemExit)
                time.sleep(0.1)
            thread.join()
            test_desc.status = TEST_STATUS_FAULT
            print(f"The test has been terminated by timeout {timeout_sec} seconds")

    def _test_execution_in_thread(self, test_desc):
        params_for_xfers = {
            "default": self._test_context.env["connection"]["transport"],
            "force_static_arp": self._test_context.env["connection"]["force_static_arp"],
            "edcl_timeout": self._test_context.env["connection"]["edcl_timeout"]
        }
        if self._test_context.env["connection"]["edcl_ip"]:
            params_for_xfers["edcl_ip"] = self._test_context.env["connection"]["edcl_ip"]
        if self._test_context.env["connection"]["edcl_mac"]:
            params_for_xfers["edcl_mac"] = self._test_context.env["connection"]["edcl_mac"]
        term = terminal(self._test_context.env["connection"]["port"], self._test_context.env["connection"]["baud"], xferparams=params_for_xfers)
        term.set_chip(self._test_context.chip)
        term.xfer.selectTransport(self._test_context.env["connection"]["transport"])

        reset = self._test_context.resets[self._test_context.env["reset"]["name"]](term, self._test_context.env["reset"])

        try:
            test = test_desc.test_class(test_desc.name, test_desc.full_name, term, reset, self._test_context.env, test_desc.params, self._user_interaction)
            if test.run():
                test_desc.status = TEST_STATUS_PASSED
        except Exception:
            print(traceback.format_exc())
        # ??? for term deleting (must be fixed in the terminal class)
        term.xfer.xfers = None
        term.xfer.how = None
        term.xfer.xfer = None
        term.xfer = None
        term.opf.objects = None
        term.opf = None
        term.ser.write = None
        term.ser = None
        # ???


def _async_raise(tid, exctype):
    '''Raises an exception in the threads with id tid'''
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # "if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
