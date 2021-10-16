"""Classes that represent the context used in advising tasks."""
from .serialization import SerializableValue


class Context(SerializableValue):
    """
    Class for representing the context for advising tasks.

    The context contains of a set of arbitrary key-value mappings that can be used
    by the `Advice` classes to store state or communicate with other advices.


    """

    def __init__(self, attributes=None):
        self._attributes = attributes or {}

    def serialized(self):
        data = {
            'attributes': self._attributes,
        }
        return data

    @classmethod
    def deserialize(cls, values):
        return Context(values['attributes'])

    @property
    def attributes(self):
        """
        A set of arbitrary key-value mappings for the `Advice` classes.

        `Advice` can add to this mapping and use this as a way of keeping state.
        """
        return self._attributes

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self._attributes == other._attributes
