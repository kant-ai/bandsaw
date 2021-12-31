"""Tracking backend using filesystem"""
import json

import logging
import pathlib
import shutil

from bandsaw.tracking.backend import Backend


logger = logging.getLogger(__name__)


class FileSystemBackend(Backend):
    """Tracking backend that stores data in the local file system."""

    def __init__(self, directory):
        """
        Create a new backend.

        Args:
            directory (str): Directory where the tracking data will be stored.
        """
        self.directory = pathlib.Path(directory)
        logger.info("Tracking sessions in directory '%s'", self.directory)
        super().__init__()

    def track_run(self, ids, run_info):
        run_dir = self.directory / 'runs' / ids.run_id
        run_dir.mkdir(parents=True)
        run_info_path = run_dir / 'run-info.json'
        with run_info_path.open('w') as stream:
            json.dump(run_info, stream)

    def track_task(self, ids, task_info):
        task_dir = self.directory / 'tasks' / ids.task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        task_info_path = task_dir / 'task-info.json'
        with task_info_path.open('w') as stream:
            json.dump(task_info, stream)

    def track_execution(self, ids, execution_info):
        execution_dir = self.directory / 'tasks' / ids.task_id / ids.execution_id
        execution_dir.mkdir(parents=True, exist_ok=True)
        execution_info_path = execution_dir / 'execution-info.json'
        with execution_info_path.open('w') as stream:
            json.dump(execution_info, stream)

    def track_session(self, ids, session_info):
        self._store_session_info(ids, session_info)
        self._store_session_for_run(ids)

    def track_result(self, ids, result_info):
        self._store_session_result(ids, result_info)

    def track_attachments(self, ids, attachments):
        self._store_session_attachments(ids, attachments)

    def _store_session_for_run(self, ids):
        run_dir = self.directory / 'runs' / ids.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        run_session_file = run_dir / str(ids)
        run_session_file.touch()

    def _store_session_info(self, ids, session_info):
        session_dir = (
            self.directory / 'tasks' / ids.task_id / ids.execution_id / ids.run_id
        )
        session_dir.mkdir(parents=True, exist_ok=True)
        session_info_file = session_dir / 'session-info.json'
        with session_info_file.open('w') as stream:
            json.dump(session_info, stream)

    def _store_session_result(self, ids, result_info):
        session_dir = (
            self.directory / 'tasks' / ids.task_id / ids.execution_id / ids.run_id
        )
        session_dir.mkdir(parents=True, exist_ok=True)
        session_info_file = session_dir / 'result-info.json'
        with session_info_file.open('w') as stream:
            json.dump(result_info, stream)

    def _store_session_attachments(self, ids, attachments):
        session_dir = (
            self.directory / 'tasks' / ids.task_id / ids.execution_id / ids.run_id
        )
        attachments_dir = session_dir / 'attachments'
        attachments_dir.mkdir(parents=True)
        for name, attachment in attachments.items():
            attachment_path = attachments_dir / name
            with attachment.open() as input_stream:
                with attachment_path.open('wb') as output_stream:
                    shutil.copyfileobj(input_stream, output_stream)
