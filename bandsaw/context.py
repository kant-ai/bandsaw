"""Classes that represent the context used in advising tasks."""
import collections.abc

from .serialization import SerializableValue


class Context(collections.abc.MutableMapping, SerializableValue):
    """
    Class for representing the context for advising tasks.

    The context contains of a set of arbitrary key-value mappings that can be used
    by the `Advice` classes to store state or communicate with other advices.

    As a default, non-existing properties return a `Context` themselves, which allows
    setting values within a hierarchy, without the need to check for the existence of
    parent contexts:

    Examples:
        >>> context = Context()
        >>> context['a']['b'] = 1

    Note:
        If a value has been set once, it can't be overwritten or removed!
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

    def __getitem__(self, key):
        if key in self._attributes:
            return self._attributes[key]
        else:
            child_context = Context()
            self._attributes[key] = child_context
            return child_context

    def __setitem__(self, key, item):
        if key in self._attributes:
            raise TypeError("Overwriting values in Context is not supported.")

        self._attributes[key] = item

    def __iter__(self):
        return iter(self.attributes)

    def __delitem__(self, key):
        raise TypeError("Deleting values from Context is not supported.")

    def __len__(self):
        return len(self._attributes)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self._attributes == other._attributes
