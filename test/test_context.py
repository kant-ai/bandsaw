import unittest

from bandsaw.context import Context


class TestContext(unittest.TestCase):

    def setUp(self):
        pass

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


if __name__ == '__main__':
    unittest.main()
