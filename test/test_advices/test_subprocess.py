import os
import pathlib
import shutil
import unittest.mock

from bandsaw.advices.subprocess import SubprocessAdvice
from bandsaw.config import Configuration
from bandsaw.interpreter import Interpreter
from bandsaw.execution import Execution
from bandsaw.serialization.json import JsonSerializer
from bandsaw.session import Session
from bandsaw.tasks import Task


def _get_pid():
    return os.getpid()


advice_test_directory = os.path.dirname(__file__)
sitecustomize_directory = os.path.join(advice_test_directory, 'subprocess_site')
test_directory = os.path.dirname(advice_test_directory)
project_directory = os.path.dirname(test_directory)

interpreter = Interpreter(
    path=[
        test_directory, project_directory, sitecustomize_directory,
    ]
)
# environment variable and sitecustomize is necessary for enabling coverage
# reporting in subprocess
interpreter.set_environment(COVERAGE_PROCESS_START=project_directory+'/tox.ini')
advice = SubprocessAdvice(
    interpreter=interpreter
)
configuration = Configuration()
configuration.add_advice_chain(advice)
configuration.set_serializer(JsonSerializer())


class TestSubprocessAdvice(unittest.TestCase):

    @staticmethod
    def tearDownClass():
        global advice
        shutil.rmtree(advice.directory)

    def test_task_is_run_in_different_process(self):
        session = Session(Task.create_task(_get_pid), Execution('r'), configuration)
        session.initiate()
        subprocess_pid = session.result.value

        self.assertNotEqual(subprocess_pid, os.getpid())

    def test_directory_for_data_exchange_can_be_configured(self):
        path = pathlib.Path('/my/directory')
        the_advice = SubprocessAdvice(directory=path)
        self.assertEqual(the_advice.directory, path)

    def test_after_does_not_proceed_or_conclude(self):
        session_mock = unittest.mock.Mock()
        the_advice = SubprocessAdvice()
        the_advice.after(session_mock)

        session_mock.proceed.assert_not_called()
        session_mock.conclude.assert_not_called()


if __name__ == '__main__':
    unittest.main()
