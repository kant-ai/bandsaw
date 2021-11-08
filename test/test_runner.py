import pathlib
import subprocess
import sys
import tempfile
import unittest.mock
import zipfile

from bandsaw.runner import create_runner_archive, main


class TestCreateRunnerArchive(unittest.TestCase):

    def setUp(self):
        self.archive_path = pathlib.Path(tempfile.mktemp())

    def tearDown(self):
        self.archive_path.unlink()

    def test_executable_is_created(self):
        create_runner_archive(self.archive_path)

        self.assertTrue(self.archive_path.exists())

    def test_executable_is_zip(self):
        create_runner_archive(self.archive_path)

        self.assertTrue(zipfile.is_zipfile(self.archive_path))

    def test_executable_is_zip(self):
        create_runner_archive(self.archive_path)

        self.assertTrue(zipfile.is_zipfile(self.archive_path))

    def test_executable_is_executable_with_python(self):
        create_runner_archive(self.archive_path)

        subprocess.check_call(
            [
                sys.executable,
                str(self.archive_path),
                '-h',
            ],
        )

    def test_executable_contains_additional_modules(self):
        create_runner_archive(self.archive_path, ['argparse'])
        with zipfile.ZipFile(self.archive_path, 'r') as archive:
            self.assertTrue('argparse.py' in archive.namelist())


class TestMain(unittest.TestCase):

    def setUp(self):
        self.input = pathlib.Path(tempfile.mkstemp()[1])
        self.output = pathlib.Path(tempfile.mkstemp()[1])

    def tearDown(self):
        self.input.unlink()
        self.output.unlink()

    @unittest.mock.patch('bandsaw.runner.Session')
    def test_main(self, session_mock):
        main(args=[
            '--input',
            str(self.input),
            '--output',
            str(self.output),
        ])


if __name__ == '__main__':
    unittest.main()
