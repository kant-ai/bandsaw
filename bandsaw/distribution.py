"""
Contains functions for creating distribution archives.

Distribution archives are the way how bandsaw transfers code between different
machines. They are normal zip files, that contain bandsaw itself, a __main__ module
which allows to execute the archive and to continue sessions and possibly some
additional dependencies.
"""
import logging
import pathlib
import sys
import tempfile
import zipfile


logger = logging.getLogger(__name__)


def _add_module_to_archive(module, archive):
    logger.info(
        "Adding module %s to distribution archive from %s",
        module.__name__,
        module.__file__,
    )

    if module.__file__.endswith('__init__.py'):
        # add the whole package
        package_dir = pathlib.Path(module.__file__).parent
        root_dir = package_dir.parent
        directories_to_package = [package_dir]
        while directories_to_package:
            directory = directories_to_package.pop()
            for path in directory.iterdir():
                if path.is_dir():
                    if path.name != '__pycache__':
                        directories_to_package.append(path)
                else:
                    archive.write(str(path.absolute()), str(path.relative_to(root_dir)))
    elif module.__file__.endswith('__main__.py'):
        # ignore because we create a new __main__.py later
        pass
    else:
        # add the module directly
        archive.write(module.__file__, pathlib.Path(module.__file__).name)


def _add_main_module(archive):
    logger.info("Adding main module to distribution archive")
    main_module_contents = """
import sys
import bandsaw.runner

if __name__ == '__main__':
    bandsaw.runner.main(sys.argv[1:])
"""
    archive.writestr('__main__.py', main_module_contents)


def _create_distribution_archive(path, modules=None):
    """
    Create an distribution archive which can execute sessions.

    This function creates a python executable archive [1] that contains the code to
    continue a session. It adds the `bandsaw` package to the archive automatically,
    but the caller can add additional packages as well.

    [1] https://docs.python.org/3/library/zipapp.html

    Args:
        path (pathlib.Path): A path where the executable is written to.
        modules (List[str]): A list of module names, that should be available to the
            executable. Defaults to `None` which doesn't add any additional packages.
    """
    logger.info("Create distribution archive in file %s", path)
    with zipfile.ZipFile(path, 'w') as archive:
        for module in modules or []:
            _add_module_to_archive(sys.modules[module], archive)
        _add_main_module(archive)


class _DistributionArchiveCache:
    """
    Internal cache that caches DistributionArchives within process
    """

    def __init__(self):
        self._cache = {}

    def get_archive(self, configuration):
        """
        Returns a distribution archive for a configuration, if in cache.

        Args:
            configuration (bandsaw.config.Configuration): Configuration for which the
                distribution archive is requested.

        Returns:
            bandsaw.distribution.DistributionArchive: The distribution archive for the
                given configuration if in the cache, otherwise `None`.
        """
        return self._cache.get(configuration)

    def put_archive(self, configuration, archive):
        """
        Puts a distribution archive to the cache.

        Args:
            configuration (bandsaw.config.Configuration): Configuration for which the
                distribution archive is added.
            archive (bandsaw.distribution.DistributionArchive): The distribution
                archive for the given configuration.
        """
        self._cache[configuration] = archive


_CACHE = _DistributionArchiveCache()


def get_distribution_archive(configuration):
    """
    Returns a distribution archive for a given configuration.

    Args:
        configuration (bandsaw.config.Configuration): The configuration for which the
            distribution package should be returned.

    Returns:
        bandsaw.distribution.DistributionArchive: The archive for the configuration.
    """
    archive = _CACHE.get_archive(configuration)
    if archive is None:
        archive_path = pathlib.Path(
            tempfile.mktemp(suffix='.pyz', prefix='distribution-')
        )
        modules = [
            '__main__',
            'bandsaw',
            configuration.module_name,
            *configuration.distribution_modules,
        ]
        archive = DistributionArchive(archive_path, *modules)
        _CACHE.put_archive(configuration, archive)
    return archive


class DistributionArchive:
    """
    Class that represents a distribution archive.

    A distribution archive contains all the code necessary for running a task. It can
    be used for running a task on a different machine by copying over the archive.

    Attributes:
        path (pathlib.Path): The path to the file containing the code.
        modules (tuple[str]): The names of the modules that are included in this
            archive.
    """

    def __init__(self, path, *modules):
        self._path = path
        self.modules = modules

    @property
    def path(self):
        """
        Returns:
            pathlib.Path: The path to the archive file. The file itself is created
                lazily, when the path is accessed the first time. This makes sure,
                we only create the archive if necessary.
        """
        if not self._path.exists():
            _create_distribution_archive(self._path, self.modules)
        return self._path

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.modules == other.modules

    def __hash__(self):
        return hash(self.modules)
