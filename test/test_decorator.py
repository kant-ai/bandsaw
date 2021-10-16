import os
import unittest

from bandsaw.config import Configuration, CONFIGURATION_MODULE_ENV_VARIABLE
from bandsaw.decorator import task


def function_without_arguments():
    return {'without': 'arguments'}


def function_raises_exception():
    raise ValueError('My error')


configuration = Configuration()


class TestTask(unittest.TestCase):

    def setUp(self):
        os.environ[CONFIGURATION_MODULE_ENV_VARIABLE] = __name__

    def tearDown(self):
        del os.environ[CONFIGURATION_MODULE_ENV_VARIABLE]

    def test_decorator_without_arguments(self):
        decorated_function = task(function_without_arguments)

        result = decorated_function()

        self.assertEqual(result, {'without': 'arguments'})

    def test_decorator_with_arguments(self):
        decorated_function = task(my='argument')(function_without_arguments)

        result = decorated_function()

        self.assertTrue(result, {'with': 'arguments'})

    def test_decorator_fails_with_invalid_configuration(self):
        with self.assertRaisesRegex(ModuleNotFoundError, "No module"):
            task(config='not_existing_config')

    def test_decorator_check_existence_of_chain(self):
        with self.assertRaisesRegex(ValueError, "Unknown advice chain"):
            task(chain='not-existing')(function_without_arguments)

    def test_decorator_sets_configuration_on_decorated_function(self):
        decorated_function = task(function_without_arguments)

        task_configuration = decorated_function.bandsaw_configuration

        self.assertIs(task_configuration, configuration)

    def test_decorated_function_reraises_exception(self):
        decorated_function = task(function_raises_exception)

        with self.assertRaisesRegex(ValueError, 'My error'):
            decorated_function()

    def test_decorator_cant_take_more_than_one_function(self):
        with self.assertRaisesRegex(RuntimeError, "Invalid 'task' decorator"):
            task(function_raises_exception, function_without_arguments)


if __name__ == '__main__':
    unittest.main()
