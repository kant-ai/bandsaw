import os
import pathlib
import shutil
import unittest

from bandsaw.advices.subprocess import SubprocessAdvice
from bandsaw.config import Configuration
from bandsaw.interpreter import Interpreter
from bandsaw.run import Run
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


class TestCachingAdvice(unittest.TestCase):

    @staticmethod
    def tearDownClass():
        global advice
        shutil.rmtree(advice.directory)

    def test_task_is_run_in_different_process(self):
        session = Session(Task.create_task(_get_pid), Run('r'), configuration)
        session.initiate()
        subprocess_pid = session.result.value

        self.assertNotEqual(subprocess_pid, os.getpid())

    def test_directory_for_data_exchange_can_be_configured(self):
        path = pathlib.Path('/my/directory')
        the_advice = SubprocessAdvice(directory=path)
        self.assertEqual(the_advice.directory, path)


if __name__ == '__main__':
    unittest.main()
