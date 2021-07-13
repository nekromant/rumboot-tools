TEST_STATUS_NOT_EXECUTED = 0
TEST_STATUS_PASSED = 1
TEST_STATUS_FAULT = 2


class TestDesc:

    def __init__(self, test_class, params, name, full_name):
        self.test_class = test_class
        self.params = params
        self.name = name
        self.full_name = full_name
        self.suitable = False
        self.status = TEST_STATUS_NOT_EXECUTED
        self.log_text = None
