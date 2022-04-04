import datetime
import json
import logging
import sys
import unittest.mock

from bandsaw.advices.log import JsonFormatter, LoggingAdvice
from bandsaw.config import Configuration
from bandsaw.session import Session
from bandsaw.tasks import Task
from bandsaw.execution import Execution


logger = logging.getLogger(__name__)


def _create_session():
    configuration = Configuration()
    task = Task.create_task(_task_function)
    task.task_id = 't'
    return Session(task, Execution('e'), configuration)


def _task_function():
    logger.info("My log message")
    logger.debug("My debug message")


class TestJsonFormatter(unittest.TestCase):

    def setUp(self):
        self.formatter = JsonFormatter()

    def test_timestamp_uses_isoformat_with_utc(self):
        record = logging.LogRecord(
            'name', logging.INFO, '/my/path', 666, 'My log message', {}, None,
        )
        record.message = record.msg
        record.created = datetime.datetime(2021, 1, 1, 1, 1, 1, 123456, tzinfo=datetime.timezone.utc).timestamp()

        log_line = self.formatter.format(record)

        log_item = json.loads(log_line)
        self.assertEqual("2021-01-01T01:01:01.123456+00:00", log_item['timestamp'])

    def test_newlines_in_messages_are_escpaed(self):
        record = logging.LogRecord(
            'name', logging.INFO, '/my/path', 666, 'My log message with \n newline', {}, None,
        )
        record.message = record.msg

        log_line = self.formatter.format(record)

        log_item = json.loads(log_line)
        self.assertIn('My log message with \\n newline', log_line)
        self.assertEqual('My log message with \n newline', log_item['message'])

    def test_exception_info_is_added_if_set(self):
        record = logging.LogRecord(
            'name', logging.INFO, '/my/path', 666, 'My log message', {}, None,
        )
        record.message = record.msg

        try:
            raise ValueError("My value error")
        except ValueError:
            record.exc_info = sys.exc_info()

        log_line = self.formatter.format(record)

        log_item = json.loads(log_line)
        self.assertEqual(
            'ValueError: My value error',
            log_item['exception'],
        )
        self.assertIn(
            'bandsaw/test/test_advices/test_log.py',
            log_item['traceback'],
        )
        self.assertIn(
            'raise ValueError("My value error")',
            log_item['traceback'],
        )

    def test_ids_are_added_if_session_is_set(self):

        record = logging.LogRecord(
            'name', logging.INFO, '/my/path', 666, 'My log message', {}, None,
        )
        record.message = record.msg
        record.session = _create_session()

        log_line = self.formatter.format(record)

        log_item = json.loads(log_line)
        self.assertEqual("t", log_item['taskId'])
        self.assertEqual("e", log_item['executionId'])
        self.assertIn('sessionId', log_item)
        self.assertIn('runId', log_item)


class TestLoggingAdvice(unittest.TestCase):

    def test_before_logs_and_proceeds(self):
        with unittest.mock.patch('bandsaw.advices.log.logger') as logger_mock:
            advice = LoggingAdvice()
            session = _create_session()
            with unittest.mock.patch.object(session, 'proceed') as proceed_mock:
                advice.before(session)

            proceed_mock.assert_called()
            logger_mock.info.assert_called()

    def test_after_logs_and_proceeds(self):
        with unittest.mock.patch('bandsaw.advices.log.logger') as logger_mock:
            advice = LoggingAdvice()
            session = _create_session()
            log_path = session.temp_dir / 'session.log'
            log_path.touch()
            with unittest.mock.patch.object(session, 'proceed') as proceed_mock:
                advice.after(session)

            proceed_mock.assert_called()
            logger_mock.info.assert_called()

    def test_logs_are_added_as_attachment(self):
        logging.root.setLevel(logging.DEBUG)
        configuration = Configuration()
        task = Task.create_task(_task_function)
        task.task_id = 't'
        self.session = Session(task, Execution('r'), configuration)

        self.advice = LoggingAdvice()
        configuration.add_advice_chain(self.advice)

        self.session.initiate()

        with self.session.attachments['session.log'].open() as stream:
            log_content = stream.read()
        self.assertIn(b'My log message', log_content)
        self.assertIn(b'My debug message', log_content)

    def test_log_level_can_be_overridden(self):
        logging.root.setLevel(logging.DEBUG)
        configuration = Configuration()
        task = Task.create_task(_task_function)
        task.task_id = 't'
        self.session = Session(task, Execution('r'), configuration)

        self.advice = LoggingAdvice(level=logging.INFO)
        configuration.add_advice_chain(self.advice)

        self.session.initiate()

        with self.session.attachments['session.log'].open() as stream:
            log_content = stream.read()
        self.assertIn(b'My log message', log_content)
        self.assertNotIn(b'My debug message', log_content)

    def test_log_formatter_can_be_overridden(self):
        logging.root.setLevel(logging.DEBUG)
        configuration = Configuration()
        task = Task.create_task(_task_function)
        task.task_id = 't'
        self.session = Session(task, Execution('r'), configuration)

        formatter = logging.Formatter(fmt='MY FORMAT: %(message)s')
        self.advice = LoggingAdvice(formatter=formatter)
        configuration.add_advice_chain(self.advice)

        self.session.initiate()

        with self.session.attachments['session.log'].open() as stream:
            log_content = stream.read()
        self.assertIn(b'MY FORMAT: My log message', log_content)

    def test_logs_use_json_as_default_format(self):
        logging.root.setLevel(logging.INFO)
        configuration = Configuration()
        task = Task.create_task(_task_function)
        task.task_id = 't'
        self.session = Session(task, Execution('r'), configuration)

        self.advice = LoggingAdvice()
        configuration.add_advice_chain(self.advice)

        self.session.initiate()

        with self.session.attachments['session.log'].open() as stream:
            log_content = stream.read().decode('utf-8')

        lines = log_content.split('\n')
        log_item1 = json.loads(lines[1])
        self.assertIsInstance(log_item1, dict)
        self.assertEqual('My log message', log_item1['message'])
        self.assertEqual('INFO', log_item1['level'])

    def test_json_log_contains_ids(self):
        logging.root.setLevel(logging.DEBUG)
        configuration = Configuration()
        task = Task.create_task(_task_function)
        task.task_id = 't'
        session = Session(task, Execution('r'), configuration)

        self.advice = LoggingAdvice()
        configuration.add_advice_chain(self.advice)

        session.initiate()

        with session.attachments['session.log'].open() as stream:
            log_content = stream.read().decode('utf-8')

        lines = log_content.split('\n')
        log_item1 = json.loads(lines[0])
        self.assertEqual(session.task.task_id, log_item1['taskId'])
        self.assertEqual(session.execution.execution_id, log_item1['executionId'])
        self.assertEqual(session.run_id, log_item1['runId'])
        self.assertEqual(session.session_id, log_item1['sessionId'])


if __name__ == '__main__':
    unittest.main()
