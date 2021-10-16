"""A library for splitting python scripts into separate tasks"""

from .advice import Advice
from .config import Configuration, get_configuration
from .decorator import task
from .extensions import Extension
from .identifier import identifier_from_string
from .interpreter import Interpreter
from .serialization import (
    JsonSerializer,
    PickleSerializer,
    SerializableValue,
)


__version__ = "0.1-dev"
