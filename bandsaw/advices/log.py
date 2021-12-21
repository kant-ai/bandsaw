"""Contains an `Advice` implementation which adds logging"""
import datetime
import json
import logging
import traceback

from ..advice import Advice


logger = logging.getLogger(__name__)


class JsonFormatter(logging.Formatter):
    """
    Formatter that formats log records into a JSON string.
    """

    def format(self, record):
        timestamp = datetime.datetime.fromtimestamp(
            record.created,
            datetime.timezone.utc,
        )

        log_item = {
            "timestamp": datetime.datetime.isoformat(timestamp),
            "logger": record.name,
            "level": record.levelname,
            "message": record.message,
            "threadId": record.thread,
            "threadName": record.threadName,
            "processId": record.process,
            "processName": record.processName,
            "module": record.module,
            "function": record.funcName,
            "path": record.pathname,
            "line_no": record.lineno,
        }

        if record.exc_info is not None:
            log_item.update(
                {
                    'traceback': ''.join(
                        traceback.format_tb(record.exc_info[2])
                    ).strip(),
                    'exception': traceback.format_exception_only(*record.exc_info[:2])[
                        0
                    ].strip(),
                }
            )

        if hasattr(record, 'session'):
            log_item.update(
                {
                    'sessionId': record.session.session_id,
                    'runId': record.session.run_id,
                    'taskId': record.session.task.task_id,
                    'executionId': record.session.execution.execution_id,
                }
            )

        return json.dumps(log_item)


class _SessionFilter(logging.Filter):  # pylint: disable=too-few-public-methods
    """
    Filter that adds the Bandsaw session to a LogRecord.
    """

    def __init__(self, session):
        self._session = session
        super().__init__()

    def filter(self, record):
        record.session = self._session
        return True


class LoggingAdvice(Advice):
    """An Advice which adds additional logging"""

    def __init__(self, level=None, formatter=None):
        self._level = level
        if formatter is None:
            formatter = JsonFormatter()
        self._formatter = formatter

    def before(self, session):
        session_log_file_path = session.temp_dir / 'session.log'
        file_handler = logging.FileHandler(
            filename=str(session_log_file_path.absolute()),
        )
        file_handler.set_name('Handler-' + session.session_id)
        if self._level is not None:
            file_handler.setLevel(self._level)
        file_handler.setFormatter(self._formatter)
        session_filter = _SessionFilter(session)
        file_handler.addFilter(session_filter)
        logging.root.addHandler(file_handler)

        logger.info(
            "BEFORE %s:%s with context %s",
            session.task.task_id,
            session.execution.execution_id,
            session.context,
        )
        session.proceed()

    def after(self, session):
        logger.info(
            "AFTER %s:%s with context %s",
            session.task.task_id,
            session.execution.execution_id,
            session.context,
        )
        for handler in logging.root.handlers:
            if handler.get_name() == 'Handler-' + session.session_id:
                logging.root.removeHandler(handler)
                handler.flush()
        session.attachments['session.log'] = session.temp_dir / 'session.log'
        session.proceed()
