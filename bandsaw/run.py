"""Contains classes and functions around a run of tasks"""
from .serialization import SerializableValue


class Run(SerializableValue):
    """
    Class that defines a run of a `Task`.

    Attributes:
        run_id (str): A string identifying this run.
        args (tuple[Any]): The positional arguments for the task to use in this
            execution.
        kwargs (Dict[Any,Any]): The keyword arguments for the task to use in this
            execution.
    """

    def __init__(self, run_id, args=None, kwargs=None):
        self.run_id = run_id
        self.args = args or ()
        self.kwargs = kwargs or {}

    def serialized(self):
        return {
            'run_id': self.run_id,
            'args': self.args,
            'kwargs': self.kwargs,
        }

    @classmethod
    def deserialize(cls, values):
        return Run(
            values['run_id'],
            values['args'],
            values['kwargs'],
        )
