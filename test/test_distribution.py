import inspect
import pathlib
import subprocess
import sys
import tempfile
import unittest.mock
import zipfile

from bandsaw.config import Configuration
from bandsaw.distribution import get_distribution_archive, DistributionArchive


class TestGetDistributionArchive(unittest.TestCase):

    def setUp(self):
        self.config = Configuration()

    def test_archive_is_created(self):
        archive = get_distribution_archive(self.config)
        self.assertIsNotNone(archive)

    def test_archive_contains_additional_modules(self):
        self.config.add_modules_for_distribution('argparse')
        archive = get_distribution_archive(self.config)
        self.assertTrue('argparse' in archive.modules)


class TestDistributionArchive(unittest.TestCase):

    def setUp(self):
        self.path = pathlib.Path(tempfile.mktemp())

    def tearDown(self):
        if self.path.exists():
            self.path.unlink()

    def test_archive_can_be_defined(self):
        archive = DistributionArchive(self.path)

    def test_two_archives_with_the_same_modules_are_equal(self):
        archive1 = DistributionArchive(self.path)
        archive2 = DistributionArchive(self.path)

        self.assertEqual(archive1, archive2)

    def test_archive_is_unequal_with_other_types(self):
        archive = DistributionArchive(self.path)

        self.assertNotEqual(archive, self.path)

    def test_two_equal_archives_have_the_same_hash(self):
        archive1 = DistributionArchive(self.path)
        archive2 = DistributionArchive(self.path)

        self.assertEqual(hash(archive1), hash(archive2))

    def test_is_created_when_path_is_accessed(self):
        archive = DistributionArchive(self.path)

        self.assertFalse(self.path.exists())

        path = archive.path

        self.assertTrue(self.path.exists())
        self.assertEqual(path, self.path)

    def test_archive_is_not_updated_with_subsequent_gets(self):
        archive = DistributionArchive(self.path)
        path1 = archive.path

        path1_mod_time = path1.stat().st_mtime_ns

        path2 = archive.path
        path2_mod_time = path2.stat().st_mtime_ns
        self.assertEqual(path1_mod_time, path2_mod_time)

    def test_archive_is_zip(self):
        archive = DistributionArchive(self.path)
        path = archive.path
        self.assertTrue(zipfile.is_zipfile(path))

    def test_archive_is_executable_with_python(self):
        archive = DistributionArchive(self.path)
        path = archive.path

        subprocess.check_call(
            [
                sys.executable,
                str(path),
                '-h',
            ],
        )

    def test_archive_contains_individual_modules(self):
        archive = DistributionArchive(self.path, 'argparse')
        path = archive.path

        with zipfile.ZipFile(path, 'r') as archive:
            self.assertTrue('argparse.py' in archive.namelist())

    def test_archive_contains_whole_packages(self):
        archive = DistributionArchive(self.path, 'bandsaw')
        path = archive.path

        with zipfile.ZipFile(path, 'r') as archive:
            self.assertTrue('bandsaw/__init__.py' in archive.namelist())
            self.assertTrue('bandsaw/config.py' in archive.namelist())

    def test_archive_contains_its_own_main_module(self):
        main_module = sys.modules['__main__']

        current_main_module_source = inspect.getsource(main_module)

        archive = DistributionArchive(self.path, '__main__')
        path = archive.path

        with zipfile.ZipFile(path, 'r') as archive:
            archive_main_source = archive.read('__main__.py').decode('utf-8')
            self.assertNotEqual(current_main_module_source, archive_main_source)


if __name__ == '__main__':
    unittest.main()
