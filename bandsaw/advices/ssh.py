"""Contains code for running tasks remotely via SSH"""
import abc
import io
import logging
import os
import pathlib
import subprocess

from bandsaw.advice import Advice
from bandsaw.user import get_current_username


logger = logging.getLogger(__name__)


class SshBackend(abc.ABC):
    """
    Interface definition for different SSH backends.
    """

    def create_dir(self, remote, remote_path):
        """
        Create a directory on a remote machine.

        Args:
            remote (bandsaw.advices.ssh.Remote): Remote machine where a directory will
                be created.
            remote_path (str): Remote path to the directory that should be created.
        """

    def copy_file_to_remote(self, remote, local_path, remote_path):
        """
        Copies a local file or directory to a remote machine.

        Args:
            remote (bandsaw.advices.ssh.Remote): Remote machine to which a file should
                be copied.
            local_path (pathlib.Path): Local path to the file which should be copied
                over.
            remote_path (pathlib.Path): Remote path of the file where it should be
                copied to.
        """

    def copy_file_from_remote(self, remote, remote_path, local_path):
        """
        Copies a remote file or directory to the local file system.

        Args:
            remote (bandsaw.advices.ssh.Remote): Remote machine from which a file
                should be copied.
            remote_path (pathlib.Path): Remote path of the file which should be
                copied.
            local_path (pathlib.Path): Local path to the file where it should be
                copied to.
        """

    def execute_remote(self, remote, executable, *arguments):
        """
        Executes an executable on a remote machine.

        Args:
            remote (bandsaw.advices.ssh.Remote): Remote machine where `executable`
                will be executed.
            executable (str): Remote path of the executable which should be executed.
            *arguments (str): Positional arguments which are the command line
                parameter for the `executable`.

        Raises:
            subprocess.CalledProcessError: If the remote process ends with an error.
                Its return code will be available through the exception.
        """

    def delete_dir(self, remote, remote_path):
        """
        Delete a directory on a remote machine.

        Args:
            remote (bandsaw.advices.ssh.Remote): Remote machine where a directory will
                be deleted.
            remote_path (str): Remote path to the directory that should be deleted.
        """


class SshCommandLineBackend(SshBackend):
    """
    SSH backend that uses the SSH command line tools.
    """

    def create_dir(self, remote, remote_path):
        return self._run(
            [
                'ssh',
                '-p',
                str(remote.port),
            ]
            + self._key_file_option(remote)
            + [
                self.login(remote),
                'mkdir',
                '-p',
                str(remote_path),
            ]
        )

    def copy_file_to_remote(self, remote, local_path, remote_path):
        copy_destination = self.get_remote_path(remote, remote_path)
        self._run(
            [
                'scp',
                '-P',
                str(remote.port),
            ]
            + self._key_file_option(remote)
            + [
                str(local_path),
                copy_destination,
            ],
        )

    def copy_file_from_remote(self, remote, remote_path, local_path):
        copy_source = self.get_remote_path(remote, remote_path)
        self._run(
            [
                'scp',
                '-P',
                str(remote.port),
            ]
            + self._key_file_option(remote)
            + [
                copy_source,
                str(local_path),
            ],
        )

    def execute_remote(self, remote, executable, *arguments):
        return self._run(
            [
                'ssh',
                '-p',
                str(remote.port),
            ]
            + self._key_file_option(remote)
            + [
                self.login(remote),
                str(executable),
            ]
            + list(arguments),
        )

    def delete_dir(self, remote, remote_path):
        return self._run(
            [
                'ssh',
                '-p',
                str(remote.port),
            ]
            + self._key_file_option(remote)
            + [
                self.login(remote),
                'rm',
                '-Rf',
                str(remote_path),
            ]
        )

    @staticmethod
    def _run(command):
        logger.debug("running command %s", command)
        subprocess.check_call(command)

    @staticmethod
    def login(remote):
        """Returns the destination of the remote in form of <user>@<host>"""
        return f"{remote.user}@{remote.host}"

    def get_remote_path(self, remote, path):
        """Returns the remote path in form of <user>@<host>:<path>"""
        return f"{self.login(remote)}:{path.absolute()}"

    @staticmethod
    def _key_file_option(remote):
        if remote.key_file is not None:
            return [
                '-i',
                remote.key_file,
            ]
        return []


class Remote:  # pylint: disable=too-few-public-methods
    """
    Definition of a remote machine.

    Remotes are used for executing sessions on remote machines.

    Attributes:
        host (str): The hostname of the machine, where this interpreter is run.
        port (int): The port where ssh is listening for connections. Defaults to 22.
        user (str): The name of the user, under which the interpreter will run.
            Defaults to the name of the local user.
        key_file (str): Path to a file containing the key to use for authentication.
        interpreter (bandsaw.interpreter.Interpreter): The interpreter which should be
            used, including its executable and python path.
        directory (str): Remote directory where temporary files are stored. If `None`,
            defaults to '/tmp'.
    """

    def __init__(
        self,
        host=None,
        port=None,
        user=None,
        key_file=None,
        interpreter=None,
        directory=None,
    ):  # pylint: disable=too-many-arguments
        if host is None:
            raise ValueError("Remote needs a host, `None` given.")
        self.host = host
        self.port = port or 22
        self.user = user or get_current_username()
        self.key_file = key_file
        if interpreter is None:
            raise ValueError("Remote needs an interpreter, `None` given.")
        self.interpreter = interpreter
        self.directory = pathlib.Path(directory or '/tmp')


class SshAdvice(Advice):
    """Advice that moves and proceeds a session on a remote machine via SSH"""

    def __init__(self, directory=None, backend=SshCommandLineBackend()):
        """
        Create a new instance.

        Args:
            directory (str): The local directory where temporary files are stored to
                exchange data between the local and the remote machine. If `None`, the
                temporary directory from the session is used.
        """
        if directory is None:
            self.directory = None
            logger.info("Using session temporary directory for exchange data")
        else:
            self.directory = pathlib.Path(directory)
            logger.info("Using directory %s for exchange data", self.directory)

        self.remotes = {}
        self._backend = backend
        super().__init__()

    def add_remote(self, remote, name='default'):
        """
        Add a new definition of a remote machine.

        Args:
            remote (bandsaw.advices.ssh.Remote): Definition of the remote machine.
            name (str): Name of the remote. Defaults to `default`.

        Returns:
            bandsaw.advices.ssh.SshAdvice: The advice with the added remote.
        """
        self.remotes[name] = remote
        return self

    def before(self, session):

        temp_dir = self.directory or session.temp_dir

        session_in_path = temp_dir / f'session-{session.session_id}-in.zip'
        session_out_path = temp_dir / f'session-{session.session_id}-out.zip'

        logger.info("Writing session to %s", session_in_path)
        with io.FileIO(str(session_in_path), mode='w') as stream:
            session.save(stream)

        parameters = session.task.advice_parameters
        remote_name = parameters.get('ssh', {}).get('remote', 'default')
        remote = self.remotes[remote_name]

        remote_run_directory = remote.directory / session.execution.execution_id
        logger.info(
            "Creating run directory %s on host %s",
            remote_run_directory,
            remote.host,
        )
        self._backend.create_dir(
            remote,
            remote_run_directory,
        )

        logger.info("Copying over distribution archive to host %s", remote.host)
        distribution_archive_path = session.distribution_archive.path
        remote_distribution_archive_path = (
            remote_run_directory / distribution_archive_path.name
        )
        self._backend.copy_file_to_remote(
            remote,
            distribution_archive_path,
            remote_distribution_archive_path,
        )

        logger.info("Copying over session to host %s", remote.host)
        remote_session_in_path = remote_run_directory / session_in_path.name
        self._backend.copy_file_to_remote(
            remote,
            session_in_path,
            remote_session_in_path,
        )

        remote_session_out_path = remote_run_directory / session_out_path.name

        logger.info(
            "Running remote process using interpreter %s", remote.interpreter.executable
        )
        self._backend.execute_remote(
            remote,
            remote.interpreter.executable,
            str(remote_distribution_archive_path),
            '--input',
            str(remote_session_in_path),
            '--output',
            str(remote_session_out_path),
            '--run-id',
            session.run_id,
        )
        # environment = self.interpreter.environment
        # environment['PYTHONPATH'] = ':'.join(self.interpreter.path)
        logger.info("Remote process exited")

        logger.info("Copying over session result from host %s", remote.host)
        self._backend.copy_file_from_remote(
            remote,
            remote_session_out_path,
            session_out_path,
        )

        logger.info(
            "Cleaning up remote directory %s on host %s",
            remote_run_directory,
            remote.host,
        )
        self._backend.delete_dir(remote, remote_run_directory)

        logger.info("Restore local session from %s", session_out_path)
        stream = io.FileIO(str(session_out_path), mode='r')
        session.restore(stream)

        logger.info(
            "Cleaning up local sessions %s, %s",
            session_in_path,
            session_out_path,
        )
        session_in_path.unlink()
        session_out_path.unlink()

        logger.info("Proceed local session")
        session.proceed()

    def after(self, session):
        logger.info("after called in process %d", os.getpid())
        logger.info("Remote process created result %s", session.result)
        logger.info("Returning to end remote session and continue in parent")
