import fnmatch


def update_suitable(test_registry, test_context):
    def update_one_test(test_desc):
        test_desc.suitable = False
        if test_context.env["tests"]["enabled"]:
            for enabled_pattern in test_context.env["tests"]["enabled"]:
                if fnmatch.fnmatch(test_desc.full_name, enabled_pattern):
                    break
            else:
                return
        if test_context.env["tests"]["disabled"]:
            for disabled_pattern in test_context.env["tests"]["disabled"]:
                if fnmatch.fnmatch(test_desc.full_name, disabled_pattern):
                    return
        test_desc.suitable = test_desc.test_class.suitable(test_context.env, test_desc.params)
    test_registry.test_iteration(update_one_test)
