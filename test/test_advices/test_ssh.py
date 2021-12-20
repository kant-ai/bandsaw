import io
import os
import pathlib
import tempfile
import unittest.mock

from bandsaw.advices.ssh import SshAdvice, Remote, SshBackend, SshCommandLineBackend
from bandsaw.config import Configuration
from bandsaw.interpreter import Interpreter
from bandsaw.execution import Execution
from bandsaw.session import Session
from bandsaw.tasks import Task


def _get_pid():
    return os.getpid()


class TestSshCommandLineBackend(unittest.TestCase):

    def setUp(self):
        self.backend = SshCommandLineBackend()
        self.remote = Remote(
            host='test.host',
            user='my_user',
            interpreter=Interpreter(
                path=[],
                executable='/usr/bin/python3',
            ),
            directory='/remote/dir',
        )
        self.remote_with_key = Remote(
            host='test.host',
            user='my_user',
            key_file='/my/key',
            interpreter=Interpreter(
                path=[],
                executable='/usr/bin/python3',
            ),
            directory='/remote/dir',
        )
        self.check_call_patcher = unittest.mock.patch(
            'bandsaw.advices.ssh.subprocess.check_call'
        )
        self.check_call_mock = self.check_call_patcher.start()

    def tearDown(self):
        self.check_call_patcher.stop()

    def test_create_dir(self):
        self.backend.create_dir(
            self.remote,
            pathlib.Path('/my/remote/path'),
        )
        self.check_call_mock.assert_called_with(
            ['ssh', '-p', '22', 'my_user@test.host', 'mkdir', '-p', '/my/remote/path'],
        )

    def test_copy_file_to_remote(self):
        self.backend.copy_file_to_remote(
            self.remote,
            pathlib.Path('/my/local/path'),
            pathlib.Path('/my/remote/path'),
        )
        self.check_call_mock.assert_called_with(
            ['scp', '-P', '22', '/my/local/path', 'my_user@test.host:/my/remote/path'],
        )

    def test_copy_file_from_remote(self):
        self.backend.copy_file_from_remote(
            self.remote,
            pathlib.Path('/my/remote/path'),
            pathlib.Path('/my/local/path'),
        )
        self.check_call_mock.assert_called_with(
            ['scp', '-P', '22', 'my_user@test.host:/my/remote/path', '/my/local/path'],
        )

    def test_execute_remote(self):
        self.backend.execute_remote(
            self.remote,
            pathlib.Path('/my/executable'),
            'argument',
        )
        self.check_call_mock.assert_called_with(
            ['ssh', '-p', '22', 'my_user@test.host', '/my/executable', 'argument'],
        )

    def test_delete_dir(self):
        self.backend.delete_dir(
            self.remote,
            pathlib.Path('/my/remote/path'),
        )
        self.check_call_mock.assert_called_with(
            ['ssh', '-p', '22', 'my_user@test.host', 'rm', '-Rf', '/my/remote/path'],
        )

    def test_create_dir_with_key_file(self):
        self.backend.create_dir(
            self.remote_with_key,
            pathlib.Path('/my/remote/path'),
        )
        self.check_call_mock.assert_called_with(
            ['ssh', '-p', '22',  '-i', '/my/key', 'my_user@test.host', 'mkdir', '-p', '/my/remote/path'],
        )

    def test_copy_file_to_remote_with_key_file(self):
        self.backend.copy_file_to_remote(
            self.remote_with_key,
            pathlib.Path('/my/local/path'),
            pathlib.Path('/my/remote/path'),
        )
        self.check_call_mock.assert_called_with(
            ['scp', '-P', '22', '-i', '/my/key', '/my/local/path', 'my_user@test.host:/my/remote/path'],
        )

    def test_copy_file_from_remote_with_key_file(self):
        self.backend.copy_file_from_remote(
            self.remote_with_key,
            pathlib.Path('/my/remote/path'),
            pathlib.Path('/my/local/path'),
        )
        self.check_call_mock.assert_called_with(
            ['scp', '-P', '22', '-i', '/my/key', 'my_user@test.host:/my/remote/path', '/my/local/path'],
        )

    def test_execute_remote_with_key_file(self):
        self.backend.execute_remote(
            self.remote_with_key,
            pathlib.Path('/my/executable'),
            'argument',
        )
        self.check_call_mock.assert_called_with(
            ['ssh', '-p', '22', '-i', '/my/key', 'my_user@test.host', '/my/executable', 'argument'],
        )

    def test_delete_dir_with_key_file(self):
        self.backend.delete_dir(
            self.remote_with_key,
            pathlib.Path('/my/remote/path'),
        )
        self.check_call_mock.assert_called_with(
            ['ssh', '-p', '22',  '-i', '/my/key', 'my_user@test.host', 'rm', '-Rf', '/my/remote/path'],
        )


class DummyBackend(SshBackend):

    def __init__(self, session):
        self.session = session

    def copy_file_to_remote(self, remote, local_path, remote_path):
        pass

    def copy_file_from_remote(self, remote, remote_path, local_path):
        # dump a session in the local file because it's expected by the test
        with io.FileIO(local_path, mode='w') as stream:
            self.session.save(stream)

    def execute_remote(self, remote, executable, *arguments):
        self.session.proceed()


class TestRemote(unittest.TestCase):

    def test_host_is_mandatory(self):
        with self.assertRaisesRegex(ValueError, "Remote needs a host"):
            Remote(host=None, interpreter=Interpreter())

    def test_interpreter_is_mandatory(self):
        with self.assertRaisesRegex(ValueError, "Remote needs an interpreter"):
            Remote(host='my.host')


class TestSshAdvice(unittest.TestCase):

    def test_task_is_run_in_different_process(self):
        config = Configuration()
        session = Session(Task.create_task(_get_pid), Execution('r'), config)
        dummy_backend = DummyBackend(session)
        backend_spy = unittest.mock.Mock(wraps=dummy_backend)
        advice = SshAdvice(
                backend=backend_spy,
            ).add_remote(
            Remote(
                host='test.host',
                user='bandsaw',
                interpreter=Interpreter(
                    path=[],
                    executable='/usr/bin/python3',
                ),
                directory='/home/bandsaw',
            ),
        )
        config.add_advice_chain(advice)

        with unittest.mock.patch("bandsaw.session.get_configuration", return_value=config):
            session.initiate()
        backend_spy.execute_remote.assert_called()
        backend_spy.copy_file_from_remote.assert_called()
        backend_spy.copy_file_to_remote.assert_called()

    def test_temp_dir_is_clean(self):
        config = Configuration()
        session = Session(Task.create_task(_get_pid), Execution('r'), config)
        dummy_backend = DummyBackend(session)
        backend_spy = unittest.mock.Mock(wraps=dummy_backend)
        temp_dir = tempfile.mkdtemp()
        advice = SshAdvice(
                backend=backend_spy,
                directory=temp_dir,
            ).add_remote(
            Remote(
                host='test.host',
                user='bandsaw',
                interpreter=Interpreter(
                    path=[],
                    executable='/usr/bin/python3',
                ),
                directory='/home/bandsaw',
            ),
        )
        config.add_advice_chain(advice)

        with unittest.mock.patch("bandsaw.session.get_configuration", return_value=config):
            session.initiate()
        self.assertEqual(0, len(list(advice.directory.iterdir())))

    def test_directory_for_data_exchange_can_be_configured(self):
        path = pathlib.Path('/my/directory')
        the_advice = SshAdvice(directory=path)
        self.assertEqual(the_advice.directory, path)

    def test_after_does_not_proceed_or_conclude(self):
        session_mock = unittest.mock.Mock()
        the_advice = SshAdvice()
        the_advice.after(session_mock)

        session_mock.proceed.assert_not_called()
        session_mock.conclude.assert_not_called()


if __name__ == '__main__':
    unittest.main()
