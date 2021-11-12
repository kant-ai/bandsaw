"""Functions for generating identifier for arbitrary python objects."""
import hashlib
import os


_ID_LENGTH = int(os.getenv('BANDSAW_ID_LENGTH', '16'))


def identifier_from_bytes(buffer):
    """
    Derive an identifier from a bytebuffer.

    Args:
        buffer (Union[bytes,bytearray]): The binary data from which to derive an
            identifier.

    Returns:
        str: The identifier in form of a string of a hexadecimal number.
    """
    identifier = hashlib.sha256(buffer).hexdigest()[:_ID_LENGTH]
    return identifier


def identifier_from_string(string):
    """
    Derive an identifier from a string.

    Args:
        string (str): The string from which to derive an identifier.

    Returns:
        str: The identifier in form of a string of a hexadecimal number.
    """
    identifier = identifier_from_bytes(string.encode('utf-8'))
    return identifier
