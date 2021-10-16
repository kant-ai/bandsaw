"""Contains code for representing the result of tasks."""

from .serialization import SerializableValue


class Result(SerializableValue):
    """
    Class to encapsulate the result of a task execution.

    Attributes:
        value (Any): The value that is returned by the task. `None` is the task raised
            an exception during execution.
        exception (Exception): The exception that was raised during execution, `None`
            if no exception was raised.
    """

    def __init__(self, value=None, exception=None):
        self.value = value
        self.exception = exception

    def serialized(self):
        values = {
            "value": self.value,
            "exception": self.exception,
        }
        return values

    @classmethod
    def deserialize(cls, values):
        value = values["value"]
        exception = values["exception"]
        return Result(value=value, exception=exception)

    def __eq__(self, other):
        value_equals = self.value == other.value
        exception_type_equals = isinstance(other.exception, type(self.exception))
        exception_args_equals = getattr(self.exception, "args", None) == getattr(
            other.exception, "args", None
        )
        return value_equals and exception_type_equals and exception_args_equals

    def __hash__(self):
        return hash((self.value, repr(self.exception)))
