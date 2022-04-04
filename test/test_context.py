import unittest

from bandsaw.context import Context


class TestContext(unittest.TestCase):

    def test_contexts_with_same_task_arguments_are_equal(self):
        context1 = Context({'a': 1})
        context2 = Context({'a': 1})

        self.assertEqual(context1, context2)

    def test_contexts_with_different_task_arguments_are_not_equal(self):
        context1 = Context({'a': 1})
        context2 = Context({'a': 2})

        self.assertNotEqual(context1, context2)

    def test_contexts_with_same_attributes_are_equal(self):
        context1 = Context({'a': 1})
        context2 = Context({'a': 1})

        self.assertEqual(context1, context2)

    def test_contexts_with_different_task_arguments_are_not_equal(self):
        context1 = Context({'a': 1})
        context2 = Context({'a': 2})

        self.assertNotEqual(context1, context2)

    def test_contexts_are_not_equal_to_other_types(self):
        context1 = Context({'a': 1})
        context2 = {'a': 1}

        self.assertNotEqual(context1, context2)

    def test_contexts_can_be_used_as_dicts_when_setting_properties(self):
        context = Context()
        context['my-value'] = 1

        self.assertEqual(context.attributes['my-value'], 1)

    def test_contexts_can_be_used_as_dicts_when_getting_properties(self):
        context = Context({'my-value': 1})

        self.assertEqual(context['my-value'], 1)

    def test_contexts_can_iterate_over_properties(self):
        context = Context({'my-value': 1, 'my-other': 2})

        keys = []
        for key in context:
            keys.append(key)

        self.assertEqual(keys, ['my-value', 'my-other'])

    def test_contexts_cant_delete_properties(self):
        context = Context({'my-value': 1})

        with self.assertRaisesRegex(TypeError, "Deleting values from Context is not supported."):
            del context['my-value']

    def test_contexts_cant_overwrite_properties(self):
        context = Context({'my-value': 1})

        with self.assertRaisesRegex(TypeError, "Overwriting values in Context is not supported."):
            context['my-value'] = 2

    def test_contexts_support_len(self):
        context = Context({'my-value': 1, 'my-other': 2})
        self.assertEqual(2, len(context))

    def test_contexts_support_len(self):
        context = Context({'my-value': 1, 'my-other': 2})
        self.assertEqual(2, len(context))

    def test_contexts_create_empty_contexts_as_default_value_for_parents(self):
        context = Context()
        context['parent']['value'] = 1

        self.assertEqual(context.attributes['parent']['value'], 1)

    def test_contexts_create_empty_contexts_as_default_value_for_parents(self):
        context = Context()
        context['parent']['value'] = 1

        self.assertEqual(context.attributes['parent']['value'], 1)


if __name__ == '__main__':
    unittest.main()
