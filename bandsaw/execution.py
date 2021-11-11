"""Contains classes and functions around an execution of a task"""
from .serialization import SerializableValue


class Execution(SerializableValue):
    """
    Class that defines an execution of a `Task`.

    It contains the arguments that should be used for the task and an unique
    identifier derived from those arguments.

    Attributes:
        execution_id (str): A string identifying this execution.
        args (tuple[Any]): The positional arguments for the task to use in this
            execution.
        kwargs (Dict[Any,Any]): The keyword arguments for the task to use in this
            execution.
    """

    def __init__(self, execution_id, args=None, kwargs=None):
        self.execution_id = execution_id
        self.args = args or ()
        self.kwargs = kwargs or {}

    def serialized(self):
        return {
            'execution_id': self.execution_id,
            'args': self.args,
            'kwargs': self.kwargs,
        }

    @classmethod
    def deserialize(cls, values):
        return Execution(
            values['execution_id'],
            values['args'],
            values['kwargs'],
        )
