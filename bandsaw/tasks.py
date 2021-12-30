"""Contains classes and functions representing different types of tasks"""
import abc
import inspect
import types

from .identifier import identifier_from_bytes, identifier_from_string
from .modules import object_as_import, import_object
from .result import Result
from .serialization import SerializableValue


class Task(SerializableValue, abc.ABC):
    """Base-class for different types of `Tasks` that can be executed

    Attributes:
        task_id (str): A unique identifier for the individual tasks.
        advice_parameters (dict): A dictionary with additional arguments provided at
            task definition.
        source (str): The python source code as string which defines the task.
        bytecode (bytes): The compiled byte code of the task definition.
    """

    # For different types of callable
    # https://stackoverflow.com/questions/19314405/how-to-detect-is-decorator-has-been-applied-to-method-or-function

    def __init__(self, task_id, advice_parameters):
        self.task_id = task_id
        self._advice_parameters = advice_parameters

    @property
    def advice_parameters(self):
        """Additional parameters for advices defined at task definition."""
        return dict(self._advice_parameters)

    @property
    @abc.abstractmethod
    def source(self):
        """The python source code as `str` which defines the task."""

    @property
    @abc.abstractmethod
    def bytecode(self):
        """The compiled byte code of the task definition as `bytes`."""

    @property
    @abc.abstractmethod
    def signature(self):
        """The signature() of the callable representing this task."""

    @abc.abstractmethod
    def _execute(self, args, kwargs):
        """
        Execute the task with the given arguments.

        Args:
            args: The positional arguments to use during execution.
            kwargs: The keyword arguments to use during execution.

        Returns:
            Any: The returned value from the task.

        Raises:
            Any: During the execution the task can raise arbitrary exceptions.
        """

    def execute(self, execution):
        """
        Execute the task with the arguments specified by the execution.

        Args:
            execution (bandsaw.execution.Execution): The definition which contains how
                the task should be executed.

        Returns:
            bandsaw.result.Result: A `Result` object with either the returned value
                from the task or an exception that was raised by the task.
        """
        try:
            result_value = self._execute(execution.args, execution.kwargs)
            result = Result(value=result_value)
        except Exception as error:  # pylint: disable=W0703 # too general exception
            result = Result(exception=error)
        return result

    @classmethod
    def create_task(cls, obj, advice_parameters=None):
        """
        Factory for creating a task for different Python objects.

        Args:
            obj (Any): Python object that should be run as a task.
            advice_parameters (dict): A dictionary containing additional arguments to
                be used by the advices.

        Returns:
            bandsaw.tasks.Task: Instance of `Task` class that allows to execute the
                task.

        Raises:
            TypeError: If there is no support for this type of python object.
        """
        if advice_parameters is None:
            advice_parameters = {}
        if isinstance(obj, types.FunctionType):
            if '.<locals>.' in obj.__qualname__:
                return _FunctionWithClosureTask(obj, advice_parameters)
            function_name, module_name = object_as_import(obj)
            return _FunctionTask(function_name, module_name, advice_parameters)
        raise TypeError(f"Unsupported task object of type {type(obj)}")


class _FunctionTask(Task):
    """
    Task class that supports free functions.
    """

    def __init__(self, function_name, module_name, advice_parameters):
        self.function_name = function_name
        self.module_name = module_name
        value = (self.function_name, self.module_name)
        task_id = identifier_from_string(repr(value))
        super().__init__(task_id, advice_parameters)

    @property
    def function(self):
        """
        The function that will be executed by the task.

        Returns:
            callable: The original function that will be executed by the task.
        """
        function = import_object(self.function_name, self.module_name)
        if hasattr(function, '__wrapped__'):
            return function.__wrapped__
        return function

    @property
    def source(self):
        return inspect.getsource(self.function)

    @property
    def bytecode(self):
        return self.function.__code__.co_code

    @property
    def signature(self):
        return inspect.signature(self.function)

    def _execute(self, args, kwargs):
        return self.function(*args, **kwargs)

    def serialized(self):
        return {
            'module_name': self.module_name,
            'function_name': self.function_name,
            'advice_parameters': self.advice_parameters,
        }

    @classmethod
    def deserialize(cls, values):
        return _FunctionTask(
            values['function_name'], values['module_name'], values['advice_parameters']
        )

    def __str__(self):
        return self.module_name + '.' + self.function_name


class _FunctionWithClosureTask(Task):
    """
    Task that can execute locally defined functions.
    """

    def __init__(self, function, advice_parameters):
        self.function = function
        super().__init__(identifier_from_bytes(self.bytecode), advice_parameters)

    @property
    def source(self):
        return inspect.getsource(self.function)

    @property
    def bytecode(self):
        return self.function.__code__.co_code

    @property
    def signature(self):
        return inspect.signature(self.function)

    def _execute(self, args, kwargs):
        return self.function(*args, **kwargs)

    def __str__(self):
        return self.function.__qualname__

    def serialized(self):
        raise NotImplementedError

    @classmethod
    def deserialize(cls, values):
        raise NotImplementedError
