"""Contains Advice implementation that runs the execution in a subprocess"""
import argparse
import io
import logging
import os
import pathlib
import subprocess
import tempfile


from ..advice import Advice
from ..interpreter import Interpreter
from ..session import Session


logger = logging.getLogger(__name__)


class SubprocessAdvice(Advice):
    """Advice that runs in a subprocess"""

    def __init__(self, directory=None, interpreter=None):
        """
        Create a new instance.

        Args:
            directory (str): The directory where temporary files are stored to
                exchange data between both processes. If `None` a temporary directory
                is used.
            interpreter (bandsaw.interpreter.Interpreter): The interpreter to use in
                the subprocess. If `None` the same interpreter will be used.
        """
        if directory is None:
            self.directory = pathlib.Path(tempfile.mkdtemp())
        else:
            self.directory = pathlib.Path(directory)
        logger.info("Using directory %s", self.directory)
        self.interpreter = interpreter or Interpreter()
        super().__init__()

    def before(self, session):
        logger.info("before called in process %d", os.getpid())

        session_id = session.run.run_id

        session_in_file, session_in_path = tempfile.mkstemp(
            '.zip', 'in-' + session_id + '-', self.directory
        )
        session_out_file, session_out_path = tempfile.mkstemp(
            '.zip', 'out-' + session_id + '-', self.directory
        )

        session.context['subprocess'] = {
            'session_in.path': session_in_path,
            'session_out.path': session_out_path,
        }

        logger.info("Writing session to %s", session_in_path)
        with io.FileIO(session_in_file, mode='w') as stream:
            session.save(stream)

        logger.info(
            "Running subprocess using interpreter %s", self.interpreter.executable
        )
        environment = self.interpreter.environment
        environment['PYTHONPATH'] = ':'.join(self.interpreter.path)
        subprocess.check_call(
            [
                self.interpreter.executable,
                '-m',
                'bandsaw.advices.subprocess',
                '--input',
                session_in_path,
                '--output',
                session_out_path,
            ],
            env=environment,
        )
        logger.info("Sub process exited")

        with io.FileIO(session_out_file, mode='r') as stream:
            session.restore(stream)
        session.proceed()

    def after(self, session):
        logger.info("after called in process %d", os.getpid())
        logger.info("Sub process created result %s", session.result)

        session_out_path = session.context['subprocess']['session_out.path']

        logger.info("Writing session with result to %s", session_out_path)
        with io.FileIO(session_out_path, mode='w') as stream:
            session.save(stream)


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input', dest='input_session', help="The context", required=True
    )
    parser.add_argument(
        '--output', dest='output_session', help="The queue", required=True
    )
    args = parser.parse_args()

    session = Session()
    with io.FileIO(args.input_session, mode='r') as stream:
        session.restore(stream)
    session.proceed()


if __name__ == '__main__':
    FORMAT = "{asctime} {process: >5d} {thread: >5d} {name} {levelname}: {message}"
    logging.basicConfig(level=logging.INFO, format=FORMAT, style='{')

    _main()
