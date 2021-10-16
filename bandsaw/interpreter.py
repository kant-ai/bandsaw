"""Contains classes regarding python interpreters"""
import sys

from .serialization import SerializableValue


class Interpreter(SerializableValue):
    """
    Class for representing different python interpreters.

    This class is used to contain the information about specific python interpreters
    that are used within the library. In order to support multiple different
    interpreters there will be the option to define the interpreter as part of config.
    Currently only a single interpreter is automatically defined.
    """

    def __init__(
        self,
        path=None,
        executable=None,
    ):
        """
        Create a new interpreter instance.

        Args:
            path (List[str]): A list of directory paths, to be used as $PYTHONPATH.
                If `None` the current `sys.path` is used.
            executable (str): The path to the python executable for this interpreter.
                If `None` the current `sys.executable` is used.
        """
        self._path = path or tuple(sys.path)
        self.executable = executable or sys.executable
        self._environment = {}

    def set_environment(self, **environment):
        """
        Set the environment variables to use for this interpreter.

        A call to this methods overwrites all variables that have been set previously.

        Args:
            **environment: Arbitrary keyword arguments where the name of the keyword
                corresponds to the name of the environment variable and the values
                will be the values set in the environment.
        """
        self._environment = environment
        return self

    @property
    def environment(self):
        """The environment variables to be set for the interpreter."""
        return dict(self._environment)

    @property
    def path(self):
        """The python path items that will be used."""
        return tuple(self._path)

    def serialized(self):
        return {
            'path': self._path,
            'executable': self.executable,
            'environment': self._environment,
        }

    @classmethod
    def deserialize(cls, values):
        return Interpreter(
            path=values['path'],
            executable=values['executable'],
        ).set_environment(**values['environment'])
