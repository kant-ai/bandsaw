import json
import pathlib
import shutil
import tempfile
import unittest

from bandsaw.session import Attachments, Ids
from bandsaw.tracking.filesystem import FileSystemBackend


class TestFileSystemBackend(unittest.TestCase):

    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.backend = FileSystemBackend(self.dir)
        self.session_id = Ids('123', '456', '789')

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_run_info_is_stored(self):
        run_dir = self.dir / 'runs' / '789'

        self.assertFalse(run_dir.exists())

        info = {'my': 'info'}
        self.backend.track_run(self.session_id, info)

        run_info_file = run_dir / 'run-info.json'
        self.assertTrue(run_info_file.exists())

        with run_info_file.open('r') as stream:
            stored_info = json.load(stream)
        self.assertEqual(info, stored_info)

    def test_task_info_is_stored(self):
        task_dir = self.dir / 'tasks' / '123'

        self.assertFalse(task_dir.exists())

        info = {'my': 'info'}
        self.backend.track_task(self.session_id, info)

        task_info_file = task_dir / 'task-info.json'
        self.assertTrue(task_info_file.exists())

        with task_info_file.open('r') as stream:
            stored_info = json.load(stream)
        self.assertEqual(info, stored_info)

    def test_execution_info_is_stored(self):
        execution_dir = self.dir / 'tasks' / '123' / '456'

        self.assertFalse(execution_dir.exists())

        info = {'my': 'info'}
        self.backend.track_execution(self.session_id, info)

        task_info_file = execution_dir / 'execution-info.json'
        self.assertTrue(task_info_file.exists())

        with task_info_file.open('r') as stream:
            stored_info = json.load(stream)
        self.assertEqual(info, stored_info)

    def test_session_info_is_stored(self):
        session_dir = self.dir / 'tasks' / '123' / '456' / '789'

        self.assertFalse(session_dir.exists())

        info = {'my': 'info'}
        self.backend.track_session(self.session_id, info)

        task_info_file = session_dir / 'session-info.json'
        self.assertTrue(task_info_file.exists())

        with task_info_file.open('r') as stream:
            stored_info = json.load(stream)
        self.assertEqual(info, stored_info)

    def test_result_info_is_stored(self):
        session_dir = self.dir / 'tasks' / '123' / '456' / '789'
        info = {'my': 'info'}
        self.backend.track_result(self.session_id, info)

        task_info_file = session_dir / 'result-info.json'
        self.assertTrue(task_info_file.exists())

        with task_info_file.open('r') as stream:
            stored_info = json.load(stream)
        self.assertEqual(info, stored_info)

    def test_attachments_are_stored(self):
        _, attachment_file1 = tempfile.mkstemp(dir=self.dir)
        with open(attachment_file1, 'w') as stream:
            stream.write("Attachment 1")
        _, attachment_file2 = tempfile.mkstemp(dir=self.dir)
        with open(attachment_file2, 'w') as stream:
            stream.write("Attachment 2")

        attachments = Attachments()
        attachments['f1.txt'] = attachment_file1
        attachments['f2.txt'] = attachment_file2

        session_dir = self.dir / 'tasks' / '123' / '456' / '789'
        self.backend.track_attachments(self.session_id, attachments)

        attachments_dir = session_dir / 'attachments'
        self.assertTrue(attachments_dir.exists())

        files = list(att.name for att in attachments_dir.iterdir())
        self.assertIn('f1.txt', files)
        self.assertIn('f2.txt', files)

        with (attachments_dir / 'f1.txt').open('r') as stream:
            self.assertEqual('Attachment 1', stream.read())

        with (attachments_dir / 'f2.txt').open('r') as stream:
            self.assertEqual('Attachment 2', stream.read())


if __name__ == '__main__':
    unittest.main()
