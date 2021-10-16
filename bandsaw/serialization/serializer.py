"""Base classes for serializers which allow to serialize python values."""
import abc


class Serializer(abc.ABC):
    """Interface for `Serializer` which serialize objects"""

    @abc.abstractmethod
    def serialize(self, value, stream):
        """
        Serialize a value/object into a binary stream.

        Args:
            value (Any): The object/value to be serialized.
            stream (io.Stream): The binary stream where the serialized value is
                written.
        """

    @abc.abstractmethod
    def deserialize(self, stream):
        """
        Deserialize a value/object from a binary stream.

        Args:
            stream (io.Stream): The binary stream from where the serialized value is
                read.

        Returns:
             Any: The object/value which was deserialized.
        """
