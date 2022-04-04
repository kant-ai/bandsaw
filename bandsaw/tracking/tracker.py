"""Contains Advice that tracks task executions in a local file system."""
import logging

from bandsaw.extensions import Extension
from bandsaw.infos import value_info
from bandsaw.tracking.backend import Backend


logger = logging.getLogger(__name__)


class TrackerExtension(Extension):
    """
    Advice that tracks task executions and their data in the file system.

    Attributes:
        _backend (bandsaw.tracking.backend.Backend): The backend implementation to use.
    """

    def __init__(self, backend):
        """
        Advice that tracks task executions and their data in the file system.

        Args:
            backend (bandsaw.tracking.backend.Backend): The backend implementation to
                use.

        Raises:
            TypeError: If `backend` does not inherit from `Backend` base class.
            ValueError: If no backend is given.
        """
        if backend is None:
            raise ValueError("Backend must be set.")
        if not isinstance(backend, Backend):
            raise TypeError("`backend` is not of type `Backend`.")
        self._backend = backend
        logger.info("Tracking sessions using backend '%s'", self._backend)
        self._tracked_runs = set()
        self._tracked_tasks = set()
        self._tracked_executions = set()
        self._tracked_sessions = set()
        self._tracked_results = set()
        self._tracked_attachments = set()
        super().__init__()

    def on_session_created(self, session):
        self._track_run(session)
        self._track_task(session)
        self._track_execution(session)
        self._track_session(session)

    def on_session_finished(self, session):
        self._track_result(session)
        self._track_attachments(session)

    def _track_run(self, session):
        if session.run_id not in self._tracked_runs:
            self._backend.track_run(session.ids, {'id': session.run_id})
            self._tracked_runs.add(session.run_id)

    def _track_task(self, session):
        if session.task.task_id not in self._tracked_tasks:
            self._backend.track_task(session.ids, self._create_task_info(session))
            self._tracked_tasks.add(session.task.task_id)

    def _track_execution(self, session):
        combined_id = session.task.task_id + '_' + session.execution.execution_id
        if combined_id not in self._tracked_executions:
            self._backend.track_execution(
                session.ids, self._create_execution_info(session)
            )
            self._tracked_executions.add(combined_id)

    def _track_session(self, session):
        if session.session_id not in self._tracked_sessions:
            self._backend.track_session(session.ids, self._create_session_info(session))
            self._tracked_sessions.add(session.session_id)

    def _track_result(self, session):
        if session.session_id not in self._tracked_results:
            self._backend.track_result(session.ids, self._create_result_info(session))
            self._tracked_results.add(session.session_id)

    def _track_attachments(self, session):
        if session.session_id not in self._tracked_attachments:
            self._backend.track_attachments(session.ids, session.attachments)
            self._tracked_attachments.add(session.session_id)

    @staticmethod
    def _create_run_info(session):
        run_info = {
            'run': {
                'id': session.run_id,
            },
            'configuration': session.configuration.module_name,
            'distribution_archive': {
                'modules': session.distribution_archive.modules,
                'id': None,  # session.distribution_archive.archive_id,
            },
        }
        return run_info

    @staticmethod
    def _create_task_info(session):
        task_info = {
            'task': {
                'id': session.task.task_id,
                'definition': str(session.task),
                'advice_parameters': session.task.advice_parameters,
            },
        }
        return task_info

    def _create_execution_info(self, session):
        def _argument_infos(task, execution):
            """
            The names of the positional and keyword arguments for this task.

            Returns:
                tuple[List[str],Set[str]]: Tuple containing a list with the names of the
                    positional arguments and a set with the names of the keyword
                    arguments.
            """
            signature = task.signature
            bound_args = signature.bind(*execution.args, **execution.kwargs)
            bound_args.apply_defaults()
            all_infos = []
            for name, value in bound_args.arguments.items():
                info = value_info(value)
                info['name'] = name
                all_infos.append(info)
            return all_infos

        execution_info = self._create_task_info(session)
        execution_info['execution'] = {
            'id': session.execution.execution_id,
            'arguments': _argument_infos(session.task, session.execution),
        }
        return execution_info

    def _create_session_info(self, session):
        tracking_info = self._create_execution_info(session)
        tracking_info.update(self._create_run_info(session))
        tracking_info.update(
            {
                'session': {
                    'id': str(session.session_id),
                },
                'task': {
                    'id': session.task.task_id,
                    'definition': str(session.task),
                    'advice_parameters': session.task.advice_parameters,
                },
            }
        )
        return tracking_info

    def _create_result_info(self, session):
        def _result_value_infos(result_value):
            """
            The names of the positional and keyword arguments for this task.

            Returns:
                tuple[List[str],Set[str]]: Tuple containing a list with the names of the
                    positional arguments and a set with the names of the keyword
                    arguments.
            """
            result_value_infos = []
            if isinstance(result_value, dict):
                for name, value in result_value.items():
                    info = value_info(value)
                    info['key'] = name
                    result_value_infos.append(info)
            elif isinstance(result_value, list):
                for index, value in enumerate(result_value):
                    info = value_info(value)
                    info['index'] = index
                    result_value_infos.append(info)
            elif isinstance(result_value, tuple):
                for index, value in enumerate(result_value):
                    info = value_info(value)
                    info['index'] = index
                    result_value_infos.append(info)
            else:
                info = value_info(result_value)
                result_value_infos = info
            return result_value_infos

        result = session.result
        result_info = self._create_session_info(session)
        result_info['result'] = {}
        if result.exception:
            result_info['result']['exception'] = type(result.exception).__name__
            result_info['result']['message'] = str(result.exception)
        else:
            result_info['result']['value'] = _result_value_infos(result.value)

        return result_info
