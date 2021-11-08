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
        for directory in directories_to_package:
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


def create_distribution_archive(target_file, modules=None):
    """
    Create an distribution archive which can execute sessions.

    This function creates a python executable archive [1] that contains the code to
    continue a session. It adds the `bandsaw` package to the archive automatically,
    but the caller can add additional packages as well.

    [1] https://docs.python.org/3/library/zipapp.html

    Args:
        target_file (str): A path where the executable is written to.
        modules (List[str]): A list of module names, that should be available to the
            executable. Defaults to `None` which doesn't add any additional packages.
    """
    logger.info("Create distribution archive in file %s", target_file)

    with zipfile.ZipFile(target_file, 'w') as archive:
        _add_module_to_archive(sys.modules['bandsaw'], archive)
        for module in modules or []:
            _add_module_to_archive(sys.modules[module], archive)
        _add_main_module(archive)
