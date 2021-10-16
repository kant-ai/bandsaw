import os
import unittest

from bandsaw.config import Configuration, get_configuration, CONFIGURATION_MODULE_ENV_VARIABLE


configuration = Configuration()


class TestGetConfiguration(unittest.TestCase):

    def test_get_configuration_uses_default_module_name(self):
        with self.assertRaisesRegex(ModuleNotFoundError, "No module named 'bandsaw_config'"):
            get_configuration()

    def test_get_configuration_takes_default_module_name_from_env_variable(self):
        os.environ[CONFIGURATION_MODULE_ENV_VARIABLE] = 'custom_config'

        with self.assertRaisesRegex(ModuleNotFoundError, "No module named 'custom_config'"):
            get_configuration()

        del os.environ[CONFIGURATION_MODULE_ENV_VARIABLE]

    def test_get_configuration_uses_given_module_name(self):
        loaded_config = get_configuration(__name__)

        self.assertIs(loaded_config, configuration)

    def test_get_configuration_raises_with_unknown_module(self):
        with self.assertRaisesRegex(ModuleNotFoundError, ''):
            get_configuration('not_existing_module')

    def test_get_configuration_raises_with_invalid_config(self):
        with self.assertRaisesRegex(TypeError, ''):
            get_configuration('invalid_config_module')

    def test_get_configuration_raises_with_no_config(self):
        with self.assertRaisesRegex(LookupError, ''):
            get_configuration('no_config_module')


if __name__ == '__main__':
    unittest.main()
