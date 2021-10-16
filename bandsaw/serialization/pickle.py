"""Contains a Serializer which uses pickle for serializing values."""
import pickle

from .serializer import Serializer


class PickleSerializer(Serializer):
    """A `Serializer` which serializes objects using pickle."""

    def serialize(self, value, stream):
        """
        Serialize a value/object into a binary stream.

        Args:
            value (Any): The object/value to be serialized.
            stream (io.Stream): The binary stream where the serialized value is
                written.
        """
        pickle.dump(value, stream)

    def deserialize(self, stream):
        """
        Deserialize a value/object from a binary stream.

        Args:
            stream (io.Stream): The binary stream from where the serialized value is
                read.

        Returns:
             Any: The object/value which was deserialized.
        """
        return pickle.load(stream)
