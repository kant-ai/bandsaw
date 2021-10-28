import unittest

from bandsaw.result import Result


class TestResult(unittest.TestCase):

    def test_equals_is_true_for_different_exceptions_with_same_type_and_args(self):
        result1 = Result(exception=ValueError('My error'))
        result2 = Result(exception=ValueError('My error'))
        self.assertEqual(result1, result2)

    def test_hash_is_true_for_different_exceptions_with_same_type_and_args(self):
        result1 = Result(exception=ValueError('My error'))
        result2 = Result(exception=ValueError('My error'))
        self.assertEqual(hash(result1), hash(result2))


if __name__ == '__main__':
    unittest.main()
