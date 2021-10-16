"""Contains a Serializer that allows to serialize objects to JSON."""
import io
import json

from .serializer import Serializer
from .values import (
    ExceptionSerializer,
    SerializableValueSerializer,
    TupleSerializer,
)


class _ExtensibleJSONEncoder(json.JSONEncoder):
    def __init__(self, value_serializers=(), **kwargs):
        self.value_serializers = value_serializers
        super().__init__(**kwargs)

    def default(self, o):
        for value_serializer in self.value_serializers:
            if value_serializer.can_serialize_value(o):
                serialized_value = {
                    '_serializer': type(value_serializer).__name__,
                    'value': value_serializer.serialize_value(o),
                }
                return serialized_value
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, o)

    def iterencode(self, o, _one_shot=False):
        # Overwrite implementation to handle tuples differently
        if isinstance(o, tuple):
            o = self.default(o)
        return super().iterencode(o, _one_shot=_one_shot)


class _ExtensibleJSONDecoder(json.JSONDecoder):
    def __init__(self, value_serializers=(), **kwargs):
        self.value_serializers = {
            type(value_serializer).__name__: value_serializer
            for value_serializer in value_serializers
        }
        super().__init__(object_hook=self.decode_custom_types, **kwargs)

    def decode_custom_types(self, obj):
        """
        Method that is called if unknown types should be decoded.

        Args:
            obj:

        Returns:

        """
        if '_serializer' in obj:
            serializer_name = obj['_serializer']
            if serializer_name not in self.value_serializers:
                raise TypeError(f"Unknown serializer '{serializer_name}'")
            return self.value_serializers[serializer_name].deserialize_value(
                obj['value']
            )
        return obj


class JsonSerializer(Serializer):
    """
    A `Serializer` which serializes objects to JSON.

    Attributes:
        value_serializers (List[ValueSerializer]): A list of serializers that are used
            for serialization of custom types.
    """

    def __init__(self):
        super().__init__()
        self.value_serializers = []
        self.value_serializers.append(ExceptionSerializer())
        self.value_serializers.append(SerializableValueSerializer())
        self.value_serializers.append(TupleSerializer())

    def serialize(self, value, stream):
        """
        Serialize a value/object into a binary stream.

        Args:
            value (Any): The object/value to be serialized.
            stream (io.Stream): The binary stream where the serialized value is
                written.
        """
        text_stream = io.TextIOWrapper(stream, encoding='utf-8')
        json.dump(
            value,
            text_stream,
            cls=_ExtensibleJSONEncoder,
            value_serializers=self.value_serializers,
            allow_nan=False,
            indent=None,
            separators=(',', ':'),
            sort_keys=True,
        )
        text_stream.detach()

    def deserialize(self, stream):
        """
        Deserialize a value/object from a binary stream.

        Args:
            stream (io.Stream): The binary stream from where the serialized value is
                read.

        Returns:
             Any: The object/value which was deserialized.
        """
        text_stream = io.TextIOWrapper(stream, encoding='utf-8')
        result = json.load(
            text_stream,
            cls=_ExtensibleJSONDecoder,
            value_serializers=self.value_serializers,
        )
        text_stream.detach()
        return result
