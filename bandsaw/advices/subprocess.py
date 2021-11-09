"""Contains Advice implementation that runs the execution in a subprocess"""
import io
import logging
import os
import pathlib
import subprocess
import tempfile


from ..advice import Advice
from ..interpreter import Interpreter


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
        archive_path = session.distribution_archive.path

        logger.info("Writing session to %s", session_in_path)
        with io.FileIO(session_in_file, mode='w') as stream:
            session.save(stream)

        logger.info(
            "Continue session in subprocess using interpreter %s and "
            "distribution archive %s",
            self.interpreter.executable,
            archive_path,
        )
        environment = self.interpreter.environment
        environment['PYTHONPATH'] = ':'.join(self.interpreter.path)
        subprocess.check_call(
            [
                self.interpreter.executable,
                archive_path,
                '--input',
                session_in_path,
                '--output',
                session_out_path,
            ],
            env=environment,
        )
        logger.info("Sub process exited")

        logger.info("Reading session from %s", session_out_path)
        with io.FileIO(session_out_file, mode='r') as stream:
            session.restore(stream)

        logger.info("proceed() session in parent process")
        session.proceed()

    def after(self, session):
        logger.info("after called in process %d", os.getpid())
        logger.info("Sub process created result %s", session.result)
        logger.info("Returning to end session and continue in parent")
