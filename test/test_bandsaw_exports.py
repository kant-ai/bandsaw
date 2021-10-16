import unittest

import bandsaw


class TestExports(unittest.TestCase):

    def test_advice_is_exported(self):
        self.assertIsNotNone(bandsaw.Advice)

    def test_configuration_is_exported(self):
        self.assertIsNotNone(bandsaw.Configuration)

    def test_task_is_exported(self):
        self.assertIsNotNone(bandsaw.task)

    def test_extension_is_exported(self):
        self.assertIsNotNone(bandsaw.Extension)

    def test_json_serialization_provider_is_exported(self):
        self.assertIsNotNone(bandsaw.JsonSerializer)

    def test_pickle_serialization_provider_is_exported(self):
        self.assertIsNotNone(bandsaw.PickleSerializer)

    def test_value_serializable_is_exported(self):
        self.assertIsNotNone(bandsaw.SerializableValue)


if __name__ == '__main__':
    unittest.main()
