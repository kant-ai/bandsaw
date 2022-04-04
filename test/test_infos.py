import unittest

from bandsaw.infos import value_info


class TestValueInfo(unittest.TestCase):
    def test_value_info_for_int(self):
        info = value_info(1)
        self.assertEqual('1', info['value'])
        self.assertEqual('int', info['type'])

    def test_value_info_for_str(self):
        info = value_info('My string')
        self.assertEqual('My string', info['value'])
        self.assertEqual('str', info['type'])

    def test_value_info_for_long_str_is_abbreviated(self):
        info = value_info('My really l'+('o' * 1000)+'ng string.')
        self.assertEqual(
            'My really looooooooooooooooooooooooooooooooooo'
            'ooooooooooooooooooooooooooooooooooooooo...oong string.',
            info['value']
        )
        self.assertEqual('str', info['type'])

    def test_value_info_for_float(self):
        info = value_info(4.5)
        self.assertEqual('4.5', info['value'])
        self.assertEqual('float', info['type'])

    def test_value_info_for_boolean(self):
        info = value_info(True)
        self.assertEqual('True', info['value'])
        self.assertEqual('bool', info['type'])

    def test_value_info_for_boolean(self):
        info = value_info(True)
        self.assertEqual('True', info['value'])
        self.assertEqual('bool', info['type'])

    def test_value_info_for_tuple(self):
        info = value_info((1, 2, 'value'))
        self.assertEqual("(1, 2, 'value')", info['value'])
        self.assertEqual('tuple', info['type'])
        self.assertEqual('3', info['size'])

    def test_value_info_for_list(self):
        info = value_info([1, 2, 'value'])
        self.assertEqual("[1, 2, 'value']", info['value'])
        self.assertEqual('list', info['type'])
        self.assertEqual('3', info['size'])

    def test_value_info_for_set(self):
        info = value_info({'my', 'set'})
        self.assertEqual("['my', 'set']", info['value'])
        self.assertEqual('set', info['type'])
        self.assertEqual('2', info['size'])

    def test_value_info_for_dict(self):
        info = value_info({'my': 'dict'})
        self.assertEqual("{'my': 'dict'}", info['value'])
        self.assertEqual('dict', info['type'])
        self.assertEqual('1', info['size'])

    def test_value_info_for_None(self):
        info = value_info(None)
        self.assertEqual("None", info['value'])
        self.assertEqual('NoneType', info['type'])

    def test_value_info_for_class_instance(self):
        class MyClass:
            pass

        info = value_info(MyClass())
        self.assertRegex(info['value'], "MyClass obj",)
        self.assertEqual('TestValueInfo.test_value_info_for_class_instance.<locals>.MyClass', info['type'])

    def test_value_info_for_class_with_additional_info(self):
        class MyClass:
            def __str__(self):
                return 'MyStringRepr'

            def value_info(self):
                return {'my': 'custom', 'info': 'implementation'}

        info = value_info(MyClass())
        self.assertEqual("MyStringRepr", info['value'])
        self.assertEqual('TestValueInfo.test_value_info_for_class_with_additional_info.<locals>.MyClass', info['type'])
        self.assertEqual('custom', info['my'])
        self.assertEqual('implementation', info['info'])


if __name__ == '__main__':
    unittest.main()
