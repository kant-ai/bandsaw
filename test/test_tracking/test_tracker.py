import unittest.mock

from bandsaw.config import Configuration
from bandsaw.execution import Execution
from bandsaw.result import Result
from bandsaw.session import Session
from bandsaw.tasks import Task
from bandsaw.tracking.backend import Backend
from bandsaw.tracking.tracker import TrackerExtension


def my_function(my_arg):
    pass


class TestTrackerExtension(unittest.TestCase):

    def setUp(self):
        self.backend_mock = unittest.mock.MagicMock(spec=Backend)
        self.tracker = TrackerExtension(self.backend_mock)

    def test_missing_backend_raises(self):
        with self.assertRaisesRegex(ValueError, "Backend must be set"):
            TrackerExtension(None)

    def test_wrong_backend_type_raises(self):
        with self.assertRaisesRegex(TypeError, "is not of type `Backend`"):
            TrackerExtension('str')

    def test_tracker_on_session_created_tracks_run(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.tracker.on_session_created(session)
        self.backend_mock.track_run.assert_called()
        ids, run_info = self.backend_mock.track_run.call_args[0]
        self.assertEqual(session.ids, ids)
        self.assertIsInstance(run_info, dict)
        self.assertIn('id', run_info)

    def test_tracker_on_session_created_tracks_run_only_once(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.tracker.on_session_created(session)
        self.tracker.on_session_created(session)
        self.backend_mock.track_run.assert_called_once()

    def test_tracker_on_session_created_tracks_task(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.tracker.on_session_created(session)
        self.backend_mock.track_task.assert_called()
        ids, task_info = self.backend_mock.track_task.call_args[0]
        self.assertEqual(session.ids, ids)
        self.assertIsInstance(task_info, dict)
        self.assertEqual({
            'id': 'f751aa54092bf4890353',
            'definition': 'test_tracking.test_tracker.my_function',
            'advice_parameters': {},
        }, task_info['task'])

    def test_tracker_on_session_created_tracks_task_only_once(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.tracker.on_session_created(session)
        self.tracker.on_session_created(session)
        self.backend_mock.track_task.assert_called_once()

    def test_tracker_on_session_created_tracks_execution(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.tracker.on_session_created(session)
        self.backend_mock.track_execution.assert_called()
        ids, execution_info = self.backend_mock.track_execution.call_args[0]
        self.assertEqual(session.ids, ids)
        self.assertIsInstance(execution_info, dict)
        self.assertIn('task', execution_info)
        self.assertEqual({'arguments': [
            {'name': 'my_arg', 'size': '3', 'type': 'str', 'value': 'arg'},
        ], 'id': 'e'}, execution_info['execution'])

    def test_tracker_on_session_created_tracks_execution_only_once(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.tracker.on_session_created(session)
        self.tracker.on_session_created(session)
        self.backend_mock.track_execution.assert_called_once()

    def test_tracker_on_session_created_tracks_session(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.tracker.on_session_created(session)
        self.backend_mock.track_session.assert_called()
        ids, session_info = self.backend_mock.track_session.call_args[0]
        self.assertEqual(session.ids, ids)
        self.assertIsInstance(session_info, dict)
        self.assertIn('task', session_info)
        self.assertIn('execution', session_info)
        self.assertEqual({'id': str(session.ids)}, session_info['session'])

    def test_tracker_on_session_created_tracks_session_only_once(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        self.tracker.on_session_created(session)
        self.tracker.on_session_created(session)
        self.backend_mock.track_session.assert_called_once()

    def test_tracker_on_session_finished_tracks_result_with_str_value(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        session.result = Result(value='My return value')
        self.tracker.on_session_finished(session)
        self.backend_mock.track_result.assert_called()
        ids, result_info = self.backend_mock.track_result.call_args[0]
        self.assertEqual(session.ids, ids)
        self.assertIsInstance(result_info, dict)
        self.assertIn('task', result_info)
        self.assertIn('execution', result_info)
        self.assertIn('session', result_info)
        self.assertEqual({'value': {'size': '15', 'type': 'str', 'value': 'My return value'}}, result_info['result'])

    def test_tracker_on_session_finished_tracks_result_with_dict_value(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        session.result = Result(value={'my': 'value'})
        self.tracker.on_session_finished(session)
        self.backend_mock.track_result.assert_called()
        ids, result_info = self.backend_mock.track_result.call_args[0]
        self.assertEqual(session.ids, ids)
        self.assertIsInstance(result_info, dict)
        self.assertIn('task', result_info)
        self.assertIn('execution', result_info)
        self.assertIn('session', result_info)
        self.assertEqual({'value': [
            {'key': 'my', 'size': '5', 'type': 'str', 'value': 'value'},
        ]}, result_info['result'])

    def test_tracker_on_session_finished_tracks_result_with_list_value(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        session.result = Result(value=['my', 'dict'])
        self.tracker.on_session_finished(session)
        self.backend_mock.track_result.assert_called()
        ids, result_info = self.backend_mock.track_result.call_args[0]
        self.assertEqual(session.ids, ids)
        self.assertIsInstance(result_info, dict)
        self.assertIn('task', result_info)
        self.assertIn('execution', result_info)
        self.assertIn('session', result_info)
        self.assertEqual({'value': [
            {'index': 0, 'size': '2', 'type': 'str', 'value': 'my'},
            {'index': 1, 'size': '4', 'type': 'str', 'value': 'dict'},
        ]}, result_info['result'])

    def test_tracker_on_session_finished_tracks_result_with_value_only_once(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        session.result = Result(value='My return value')
        self.tracker.on_session_finished(session)
        self.tracker.on_session_finished(session)
        self.backend_mock.track_result.assert_called_once()

    def test_tracker_on_session_finished_tracks_result_with_exception(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        session.result = Result(exception=ValueError('My error'))
        self.tracker.on_session_finished(session)
        self.backend_mock.track_result.assert_called()
        ids, result_info = self.backend_mock.track_result.call_args[0]
        self.assertEqual(session.ids, ids)
        self.assertIsInstance(result_info, dict)
        self.assertIn('task', result_info)
        self.assertIn('execution', result_info)
        self.assertIn('session', result_info)
        self.assertEqual({'exception': 'ValueError', 'message': 'My error'}, result_info['result'])

    def test_tracker_on_session_finished_tracks_attachments(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        session.result = Result(value='My return value')
        self.tracker.on_session_finished(session)
        self.backend_mock.track_attachments.assert_called()
        ids, attachments = self.backend_mock.track_attachments.call_args[0]
        self.assertEqual(session.ids, ids)
        self.assertIs(attachments, session.attachments)

    def test_tracker_on_session_finished_tracks_attachments_only_once(self):
        session = Session(Task.create_task(my_function), Execution('e', ['arg']), Configuration())
        session.result = Result(value='My return value')
        self.tracker.on_session_finished(session)
        self.tracker.on_session_finished(session)
        self.backend_mock.track_attachments.assert_called_once()


if __name__ == '__main__':
    unittest.main()
