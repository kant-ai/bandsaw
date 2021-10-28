"""A collection of classes for serializing custom objects."""
import abc
import collections
import importlib
import logging


logger = logging.getLogger(__name__)


class ValueSerializer(abc.ABC):
    """
    Interface for serializers that can serialize custom values.
    """

    @abc.abstractmethod
    def can_serialize_value(self, value):
        """
        Returns if a serializer can serialize a specific value.

        Args:
            value (Any): The value that should be serialized.

        Returns:
            boolean: `True` if this serializer can serialize the given value,
                otherwise `False`.
        """

    @abc.abstractmethod
    def serialize_value(self, value):
        """
        Returns a serialized representation of the given value.

        The returned representation can use standard python types like primitive
        values, lists or dicts.

        Args:
            value (Any): The value that should be serialized.

        Returns:
            Any: The serialized representation of the value.
        """

    @abc.abstractmethod
    def deserialize_value(self, representation):
        """
        Returns a deserialized value from its serialized representation.

        Args:
            representation (Any): The serialized representation of the value.

        Returns:
            Any: The deserialized value.
        """


class ExceptionSerializer(ValueSerializer):
    """
    A ValueSerializer for serializing exceptions.

    The serializer saves only the type and the `args` attribute of the exception,
    therefore it won't work for all exception types, but it should cover the most.
    Other attributes of the exception, e.g. stacktrace etc. are discarded.
    """

    def can_serialize_value(self, value):
        return isinstance(value, Exception)

    def serialize_value(self, value):
        state = {
            'type': type(value).__name__,
            'module': type(value).__module__,
            'args': value.args,
        }
        return state

    def deserialize_value(self, representation):
        module_name = representation['module']
        type_name = representation['type']
        module = importlib.import_module(module_name)
        value_type = getattr(module, type_name)
        return value_type(*representation['args'])


class TupleSerializer(ValueSerializer):
    """
    A ValueSerializer for serializing tuples.

    The serializer supports normal tuples as well as named tuples. When namedtuples
    are deserialized it first tries to reuse an existing namedtople type. If the type
    can't be imported or reused, a new namedtuple type with the same name and fields
    is created on the fly.
    """

    def can_serialize_value(self, value):
        return isinstance(value, tuple)

    def serialize_value(self, value):
        if hasattr(value, '_fields'):
            state = {
                'type': 'namedtuple',
                'fields': list(value._fields),
                'name': type(value).__name__,
                'module': type(value).__module__,
                'items': list(value),
            }
        else:
            state = {
                'type': 'tuple',
                'items': list(value),
            }

        return state

    def deserialize_value(self, representation):
        if representation['type'] == 'namedtuple':
            # try to import the namedtuple type
            module_name = representation['module']
            type_name = representation['name']
            try:
                module = importlib.import_module(module_name)
                tuple_type = getattr(module, type_name)
            except (ImportError, AttributeError) as error:
                logger.warning(
                    "Error importing namedtuple, trying to recreate it: %s", error
                )
                # Recreate a new type
                field_names = ' '.join(representation['fields'])
                tuple_type = collections.namedtuple(
                    type_name, field_names, module=module_name
                )
            return tuple_type(*representation['items'])

        return tuple(representation['items'])


class SerializableValue(abc.ABC):
    """Interface for types that can serialize themselves."""

    @abc.abstractmethod
    def serialized(self):
        """Returns a serializable representation of the value."""

    @classmethod
    @abc.abstractmethod
    def deserialize(cls, values):
        """Returns a new instance of a value from its serialized representation."""


class SerializableValueSerializer(ValueSerializer):
    """
    A ValueSerializer for serializing subclasses of `SerializableValue`.

    The serializer uses the methods defined in `SerializableValue` and implemented
    by the individual classes to serialize values. It stores the type of the value
    and its serialized representation and allows to recreate the value from this
    information.
    """

    def can_serialize_value(self, value):
        return isinstance(value, SerializableValue)

    def serialize_value(self, value):
        state = {
            'type': type(value).__name__,
            'module': type(value).__module__,
            'serialized': value.serialized(),
        }
        return state

    def deserialize_value(self, representation):
        module_name = representation['module']
        type_name = representation['type']
        module = importlib.import_module(module_name)
        value_type = getattr(module, type_name)
        return value_type.deserialize(representation['serialized'])
