def update_suitable(test_registry, test_context):
    def update_one_test(test_desc):
        test_desc.suitable = test_desc.test_class.suitable(test_context.env, test_desc.params)
    test_registry.test_iteration(update_one_test)
