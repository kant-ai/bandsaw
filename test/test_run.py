import unittest

import bandsaw.run


class TestRunId(unittest.TestCase):

    def setUp(self):
        bandsaw.run._RUN_ID = None

    def test_run_id_is_automatically_defined(self):
        run_id = bandsaw.run.get_run_id()
        self.assertIsNotNone(run_id)

    def test_run_id_stays_the_same(self):
        first_run_id = bandsaw.run.get_run_id()
        second_run_id = bandsaw.run.get_run_id()
        self.assertEqual(first_run_id, second_run_id)

    def test_run_id_can_be_set(self):
        bandsaw.run.set_run_id('my-run-id')
        run_id = bandsaw.run.get_run_id()
        self.assertEqual(run_id, 'my-run-id')

    def test_setting_run_id_again_raises(self):
        bandsaw.run.set_run_id('my-first-id')
        with self.assertRaisesRegex(RuntimeError, "Run ID was already set"):
            bandsaw.run.set_run_id('my-run-id')


if __name__ == '__main__':
    unittest.main()
