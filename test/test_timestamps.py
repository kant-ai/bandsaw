import datetime
import sys
import unittest.mock

from bandsaw.config import Configuration
from bandsaw.execution import Execution
from bandsaw.session import Session
from bandsaw.tasks import Task
from bandsaw.timestamps import TimestampsExtension


def my_function(my_arg):
    pass


class TestTimestampsExtension(unittest.TestCase):

    def setUp(self):
        self.timestamps = TimestampsExtension()

    @unittest.skipIf(sys.version_info.minor < 7, "Only supported in python >= 3.7")
    def test_timestamps_are_stored_in_isoformat(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.timestamps.on_session_created(session)
        self.assertIn('timestamps', session.context)
        self.assertIn('session_created', session.context['timestamps'])
        timestamp = datetime.datetime.fromisoformat(session.context['timestamps']['session_created'])
        self.assertIsInstance(timestamp, datetime.datetime)

    def test_tracker_on_session_created_sets_timestamp(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.timestamps.on_session_created(session)
        self.assertIn('timestamps', session.context)
        self.assertIn('session_created', session.context['timestamps'])

    def test_tracker_on_session_finished_sets_timestamp(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.timestamps.on_session_finished(session)
        self.assertIn('timestamps', session.context)
        self.assertIn('session_finished', session.context['timestamps'])

    def test_tracker_on_before_task_executed_sets_timestamp(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.timestamps.on_before_task_executed(session)
        self.assertIn('timestamps', session.context)
        self.assertIn('before_task', session.context['timestamps'])

    def test_tracker_on_after_task_executed_timestamp(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.timestamps.on_after_task_executed(session)
        self.assertIn('timestamps', session.context)
        self.assertIn('after_task', session.context['timestamps'])


if __name__ == '__main__':
    unittest.main()
