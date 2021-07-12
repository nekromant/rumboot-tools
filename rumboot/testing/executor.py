import sys
import io
import threading
import inspect
import ctypes
import time
from rumboot.terminal import terminal
from rumboot.testing.test_desc import *


class TestExecutor:

    def __init__(self, test_context, user_iteraction, log_func=None):
        self._test_context = test_context
        self._user_iteraction = user_iteraction
        self._log_func = log_func
        self._log_stream = None

    def exec_test(self, test_desc):
        timeout_sec = test_desc.test_class.timeout
        if "timeout" in test_desc.params:
            timeout_sec = test_desc.params["timeout"]

        test_desc.log_text = None
        self._log_stream = io.StringIO()
        save_stdout = sys.stdout
        save_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        try:
            thread = threading.Thread(target=self._test_execution_in_thread, args=[test_desc])
            thread.start()
            thread.join(timeout=timeout_sec)

            if thread.isAlive():
                while thread.isAlive():
                    _async_raise(thread.ident, SystemExit)
                    time.sleep(0.1)
                thread.join()
                test_desc.status = TEST_STATUS_FAULT
                print(f"The test has been terminated by timeout {timeout_sec} seconds")

            if test_desc.status == TEST_STATUS_PASSED:
                print("Passed")
            elif test_desc.status == TEST_STATUS_FAULT:
                print("Fault")
            else:
                raise Exception("Unknown test status")
        finally:
            sys.stdout = save_stdout
            sys.stderr = save_stderr
        test_desc.log_text = self._log_stream.getvalue()

    # IOBase
    def write(self, text):
        self._log_stream.write(text)
        if self._log_func:
            self._log_func(text)

    # IOBase
    def flush(self):
        pass

    def _test_execution_in_thread(self, test_desc):
        reset = self._test_context.resets[self._test_context.opts.reset[0]](self._test_context.opts) # ??? opts
        term = terminal(self._test_context.env["connection"]["port"], self._test_context.env["connection"]["baud"])
        term.set_chip(self._test_context.chip)
        term.xfer.selectTransport(self._test_context.env["connection"]["transport"])
        test_desc.status = TEST_STATUS_FAULT
        try:
            test = test_desc.test_class(term, reset, self._test_context.env, test_desc.params, self._user_iteraction)
            if test.run():
                test_desc.status = TEST_STATUS_PASSED
        except Exception:
            pass


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
