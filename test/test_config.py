import os
import shutil
import unittest.mock

from bandsaw.config import Configuration, get_configuration, CONFIGURATION_MODULE_ENV_VARIABLE


configuration = Configuration()


class TestConfiguration(unittest.TestCase):

    def test_configuration_can_be_used_as_dict_keys(self):
        config = Configuration()

        my_dict = {
            config: 'value'
        }
        self.assertEqual(my_dict[config], 'value')

    def test_configuration_with_same_name_are_equal(self):
        config1 = Configuration()
        config2 = Configuration()

        self.assertEqual(config1, config2)

    def test_configuration_with_different_name_are_not_equal(self):
        config1 = Configuration()
        config1.module_name = 'my_config'
        config2 = Configuration()
        config2.module_name = 'another_config'

        self.assertNotEqual(config1, config2)

    def test_configuration_with_different_type_are_not_equal(self):
        config = Configuration()
        config.module_name = 'my_config'

        self.assertNotEqual(config, 'config')

    def test_configuration_with_same_name_have_same_hash(self):
        config1 = Configuration()
        config2 = Configuration()

        self.assertEqual(hash(config1), hash(config2))

    def test_configuration_with_different_name_are_not_equal(self):
        config1 = Configuration()
        config1.module_name = 'my_config'
        config2 = Configuration()
        config2.module_name = 'another_config'

        self.assertNotEqual(hash(config1), hash(config2))

    def test_configuration_has_existing_temp_directory(self):
        config = Configuration()
        self.assertIsNotNone(config.temporary_directory)
        self.assertTrue(config.temporary_directory.exists())
        self.assertTrue(config.temporary_directory.is_dir())

    def test_temp_directory_is_registered_for_cleaning_up(self):
        with unittest.mock.patch('bandsaw.config.atexit.register') as register_mock:
            config = Configuration()
        register_mock.assert_called_with(shutil.rmtree, str(config.temporary_directory))


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
