from rumboot.testing.context import TestContext
from rumboot.testing.registry import test_registry
from rumboot.testing.testing_cli import start_testing_cli
from rumboot.testing.testing_gui import start_testing_gui


# starts before test loading
_test_context = TestContext()
_test_context.process_cmdline()
_test_context.load_environment()


# starts after test loading
def rumboot_start_testing():
    _test_context.setup_environment()
    if _test_context.env["gui"]:
        start_testing_gui(test_registry, _test_context)
    else:
        start_testing_cli(test_registry, _test_context)
