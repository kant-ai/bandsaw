import json
import os
import sys
import unittest

import bandsaw.run
from bandsaw.user import get_current_username


class TestRun(unittest.TestCase):

    def test_new_run_contains_start_date(self):
        run = bandsaw.run.Run('my-run-id')
        self.assertIsInstance(run.start_date, str)
        self.assertRegex(run.start_date, r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}[+-]\d\d:\d\d$')

    def test_new_run_contains_current_user(self):
        run = bandsaw.run.Run('my-run-id')
        self.assertEqual(run.user, get_current_username())

    def test_new_run_contains_command(self):
        run = bandsaw.run.Run('my-run-id')
        self.assertEqual(run.command, sys.argv)

    def test_new_run_contains_environment(self):
        run = bandsaw.run.Run('my-run-id')
        self.assertEqual(run.env, os.environ)

    def test_new_run_contains_meta_data(self):
        run = bandsaw.run.Run('my-run-id', meta={'my': 'meta'})
        self.assertEqual(run.meta, {'my': 'meta'})

    def test_run_can_be_written_as_json(self):
        run = bandsaw.run.Run(
            'my-run-id',
            start_date='my-date',
            user='my-user',
            command='/my-command',
            env={'env': 'variable'},
            meta={'my': 'meta'},
        )
        json_string = json.dumps(run.to_json())
        self.assertEqual(json_string, '{"id": "my-run-id", "start_date": "my-date", "user": "my-user", "command": "/my-command", "env": {"env": "variable"}, "meta": {"my": "meta"}}')

    def test_run_can_be_recreated_from_json(self):
        run = bandsaw.run.Run(
            'my-run-id',
            start_date='my-date',
            user='my-user',
            command='/my-command',
            env={'env': 'variable'},
            meta={'my': 'meta'},
        )
        new_run = bandsaw.run.Run.from_json(run.to_json())
        self.assertEqual(run.run_id, new_run.run_id)
        self.assertEqual(run.start_date, new_run.start_date)
        self.assertEqual(run.user, new_run.user)
        self.assertEqual(run.command, new_run.command)
        self.assertEqual(run.env, new_run.env)
        self.assertEqual(run.meta, new_run.meta)


class TestGetRun(unittest.TestCase):

    def test_get_run_returns_a_run_instance(self):
        run = bandsaw.run.get_run()
        self.assertIsInstance(run, bandsaw.run.Run)

    def test_get_run_returns_the_same_instance_in_multiple_calls(self):
        run1 = bandsaw.run.get_run()
        run2 = bandsaw.run.get_run()
        self.assertIs(run1, run2)


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
