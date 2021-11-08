import pathlib
import subprocess
import sys
import tempfile
import unittest.mock
import zipfile

from bandsaw.distribution import create_distribution_archive


class TestCreateDistributionArchive(unittest.TestCase):

    def setUp(self):
        self.archive_path = pathlib.Path(tempfile.mktemp())

    def tearDown(self):
        self.archive_path.unlink()

    def test_archive_is_created(self):
        create_distribution_archive(self.archive_path)

        self.assertTrue(self.archive_path.exists())

    def test_archive_is_zip(self):
        create_distribution_archive(self.archive_path)

        self.assertTrue(zipfile.is_zipfile(self.archive_path))

    def test_archive_is_executable_with_python(self):
        create_distribution_archive(self.archive_path)

        subprocess.check_call(
            [
                sys.executable,
                str(self.archive_path),
                '-h',
            ],
        )

    def test_archive_contains_additional_modules(self):
        create_distribution_archive(self.archive_path, ['argparse'])
        with zipfile.ZipFile(self.archive_path, 'r') as archive:
            self.assertTrue('argparse.py' in archive.namelist())


if __name__ == '__main__':
    unittest.main()
