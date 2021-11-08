"""Contains functions to continue sessions from files"""
import argparse
import io
import logging
import pathlib
import sys
import zipfile

from .session import Session


logger = logging.getLogger(__name__)


def _add_module_to_archive(module, archive):
    logger.info("Adding module %s to runner archive", module.__name__)

    if module.__file__.endswith('__init__.py'):
        # add the whole package
        package_dir = pathlib.Path(module.__file__).parent
        root_dir = package_dir.parent
        directories_to_package = [package_dir]
        for directory in directories_to_package:
            for path in directory.iterdir():
                if path.is_dir():
                    directories_to_package.append(path)
                else:
                    archive.write(str(path.absolute()), str(path.relative_to(root_dir)))
    else:
        # add the module directly
        archive.write(module.__file__, pathlib.Path(module.__file__).name)


def _add_main_module(archive):
    logger.info("Adding main module to runner archive")

    main_module_contents = """
import sys
import bandsaw.runner

if __name__ == '__main__':
    bandsaw.runner.main(sys.argv[1:])
"""
    archive.writestr('__main__.py', main_module_contents)


def create_runner_archive(target_file, modules=None):
    """
    Create an runner archive which can execute sessions.

    This function creates a python executable archive [1] that contains the code to
    continue a session. It adds the `bandsaw` package to the archive automatically,
    but the caller can add additional packages as well.

    [1] https://docs.python.org/3/library/zipapp.html

    Args:
        target_file (str): A path where the executable is written to.
        modules (List[str]): A list of module names, that should be available to the
            executable. Defaults to `None` which doesn't add any additional packages.
    """
    logger.info("Create runner archive in file %s", target_file)

    with zipfile.ZipFile(target_file, 'w') as archive:
        _add_module_to_archive(sys.modules['bandsaw'], archive)
        for module in modules or []:
            _add_module_to_archive(sys.modules[module], archive)
        _add_main_module(archive)


def main(args):
    """
    Main function that can be used for proceeding a session.

    This function allows to read a session from a file, proceed it until it returns
    and then save the state of the session to a new file. It is used for running
    tasks in a separate process or on different machines.

    Args:
        args (tuple[str]): The arguments taken from the command line.
    """
    log_format = "{asctime} {process: >5d} {thread: >5d} {name} {levelname}: {message}"
    logging.basicConfig(level=logging.INFO, format=log_format, style='{')

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input',
        dest='input_session',
        help="The session which should be continued",
        required=True,
    )
    parser.add_argument(
        '--output',
        dest='output_session',
        help="The session after continuation ended",
        required=True,
    )
    args = parser.parse_args(args=args)

    logger.info("Creating new session")
    session = Session()

    logger.info("Reading session from %s", args.output_session)
    with io.FileIO(args.input_session, mode='r') as stream:
        session.restore(stream)

    logger.info("Proceeding session")
    session.proceed()

    logger.info("Writing session with result to %s", args.output_session)
    with io.FileIO(args.output_session, mode='w') as stream:
        session.save(stream)
