import unittest

from bandsaw.interpreter import Interpreter


class TestInterpreter(unittest.TestCase):

    def setUp(self):
        self.interpreter = Interpreter(
            path=['/a', '/b'],
            executable='/my/executable',
        ).set_environment(a='b')

    def test_returned_environment_doesnt_change_interpreter(self):
        env = self.interpreter.environment
        env['a'] = 'c'

        self.assertEqual(self.interpreter.environment, {'a': 'b'})

    def test_returned_path_cant_change_interpreter(self):
        path = self.interpreter.path
        path += ('/c',)

        self.assertEqual(self.interpreter.path, ('/a', '/b'))

    def test_interpreter_can_be_serialized(self):
        serialized = self.interpreter.serialized()
        deserialized = Interpreter.deserialize(serialized)

        self.assertEqual(self.interpreter.path, deserialized.path)
        self.assertEqual(self.interpreter.environment, deserialized.environment)
        self.assertEqual(self.interpreter.executable, deserialized.executable)


if __name__ == '__main__':
    unittest.main()
