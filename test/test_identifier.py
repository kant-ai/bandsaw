import json
import unittest

from bandsaw.identifier import identifier_from_string


class TestIdentifierFromString(unittest.TestCase):

    def test_single_value(self):
        values = {
            'a': 1,
        }
        identifier = identifier_from_string(json.dumps(values))
        self.assertEqual(identifier, 'f9d86028c6e0d64e225186f96acb69338b2c59764df79162107f5c4bb34d1310')

    def test_equal_instances_have_same_identifier(self):
        values1 = {
            'a': 1,
        }
        values2 = {
            'a': 1,
        }
        identifier1 = identifier_from_string(json.dumps(values1))
        identifier2 = identifier_from_string(json.dumps(values2))
        self.assertEqual(identifier1, identifier2)

    def test_order_of_values_doesnt_change_identifier(self):
        values1 = {
            'a': 1,
        }
        values1['b'] = 2
        values2 = {
            'b': 2,
        }
        values2['a'] = 1
        identifier1 = identifier_from_string(json.dumps(values1, sort_keys=True))
        identifier2 = identifier_from_string(json.dumps(values2, sort_keys=True))
        self.assertEqual(identifier1, identifier2)

    def test_derive_identfier_for_none(self):
        value = None
        identifier = identifier_from_string(json.dumps(value))
        self.assertEqual(identifier, '74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b')

    def test_cant_derive_identifier_from_unknown_types(self):
        class MyClass:
            pass

        value = MyClass()
        with self.assertRaisesRegex(TypeError, 'not JSON serializable'):
            identifier_from_string(json.dumps(value))


if __name__ == '__main__':
    unittest.main()
