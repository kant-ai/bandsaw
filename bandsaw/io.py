"""Contains classes related to input/output of data."""
import io
import logging


logger = logging.getLogger(__name__)


class BytearrayGeneratorToStream(io.RawIOBase):
    """
    Stream that reads from a generator that yields bytes/bytearrays.
    """

    def __init__(self, generator):
        self._generator = generator
        self._source = None
        self._source_position = 0
        super().__init__()

    def readinto(self, buffer):
        buffer_size = len(buffer)
        position = 0
        generator_empty = False
        while True:
            if self._source is None:
                self._source = next(self._generator, None)
                self._source_position = 0
                if self._source is None:
                    logger.debug("no new bytearray from generator, ending stream")
                    generator_empty = True
                else:
                    logger.debug(
                        "got new bytearray from generator of size %d",
                        len(self._source),
                    )
            if self._source is not None:
                source_bytes_left = len(self._source) - self._source_position

                buffer_free = buffer_size - position
                bytes_to_copy = min(buffer_free, source_bytes_left)
                logger.debug(
                    "copy %d bytes from current value to stream via buffer of size %d",
                    bytes_to_copy,
                    buffer_size,
                )
                buffer_end = position + bytes_to_copy
                source_end = self._source_position + bytes_to_copy
                buffer[position:buffer_end] = self._source[
                    self._source_position : source_end
                ]
                position += bytes_to_copy
                if bytes_to_copy < source_bytes_left:
                    self._source_position += bytes_to_copy
                else:
                    self._source = None
            buffer_full = position == buffer_size
            if buffer_full or generator_empty:
                break
        return position


def read_stream_to_generator(stream, buffer_size=8192):
    """
    Read from a stream into a generator yielding `bytes`.

    Args:
        stream (io.Stream): The stream to read bytes from.
        buffer_size (int): The buffer size to read. Each individual `bytes` buffer
            returned by the generator has a maximum size of `buffer_size`. Defaults
            to `8192` if not set.

    Yields:
        bytes: A byte buffer of maximum size of `buffer_size`.

    """
    buffer = bytearray(buffer_size)
    while True:
        read = stream.readinto(buffer)
        if read:
            yield buffer[:read]
        else:
            break
