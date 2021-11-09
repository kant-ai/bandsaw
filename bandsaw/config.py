"""Contains the class and functions to configure bandsaw."""
import importlib
import logging
import os
import traceback
import typing

from .modules import get_loaded_module_name_by_path
from .serialization import PickleSerializer


logger = logging.getLogger(__name__)


CONFIGURATION_MODULE_ENV_VARIABLE = 'BANDSAW_CONFIG_MODULE'
CONFIGURATION_MODULE_DEFAULT = 'bandsaw_config'


class Configuration:
    """
    Class that represents a configuration for bandsaw.
    """

    def __init__(self):
        self._advice_chains = {}
        self.extensions = []
        self.serializer = PickleSerializer()
        self.add_advice_chain()
        stack = traceback.extract_stack(limit=2)
        config_module_file_path = stack[0].filename
        self.module_name = get_loaded_module_name_by_path(config_module_file_path)
        logger.info("Config created in module: %s", self.module_name)
        self.distribution_modules = []

    def add_advice_chain(self, *advices, name='default'):
        """
        Add a new advice chain to the configuration.

        Each advice chain has a unique `name`. If multiple chains with the same name
        are added to the configuration, the last chain overwrites all previous chains.

        Args:
            *advices (bandsaw.advice.Advice): A tuple of advices for this chain.
            name (str): The name of the advice chain, defaults to 'default' if not
                specified.

        Returns:
            bandsaw.config.Configuration: The configuration to which the chain was
                added.

        """
        self._advice_chains[name] = advices
        return self

    def get_advice_chain(self, name):
        """
        Returns the advice chain with the given name.

        Args:
            name (str): Name of the wanted advice chain.

        Returns:
            List[bandsaw.advice.Advice]: The advice chain with the given name.

        Raises:
            KeyError: If no chain with the specified name is configured.
        """
        return self._advice_chains.get(name)

    def add_extension(self, extension):
        """
        Add an `Extension` to the configuration.

        `Extensions` are objects that can implement callbacks to be informed by
        bandsaw about certain conditions, e.g. the creation of new tasks or the final
        result of an execution.

        Args:
            extension (bandsaw.extension.Extension): An object implementing the
                `Extension`.

        Returns:
            bandsaw.config.Configuration: The configuration to which the extension was
                added.
        """
        self.extensions.append(extension)
        return self

    def set_serializer(self, serializer):
        """
        Sets the serialize which defines how tasks and results will be serialized.

        Args:
            serializer (bandsaw.serialization.Serializer): The serializer to use for
                serializing objects.

        Returns:
            bandsaw.config.Configuration: The configuration to which the extension was
                added.
        """
        self.serializer = serializer
        return self

    def add_modules_for_distribution(self, *modules):
        """
        Add modules that should be included in the distribution archive.

        Args:
            *modules (List[str]): Positional arguments with strings, that contain the
                names of modules, which should be included in the distribution
                archive.

        Returns:
            bandsaw.config.Configuration: The configuration with the added modules.
        """
        self.distribution_modules.extend(modules)
        return self

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.module_name == other.module_name

    def __hash__(self):
        return hash(self.module_name)


_configurations: typing.Dict[str, Configuration] = {}


def get_configuration(configuration_module=None):
    """
    Return a configuration.

    Args:
        configuration_module (str): The module name of a module, which contains the
            configuration. The module needs to define a member 'configuration', which
            contains an instance of `Configuration`. If no module name is given, a
            default configuration is returned based on the value of the
            `BANDSAW_CONFIG_MODULE` environment variable. If this variable is not set,
            we default to 'bandsaw_config'.

    Returns:
        bandsaw.config.Configuration: The configuration.

    Raises:
        ModuleNotFoundError: If no module exists with name `configuration_module`.
        LookupError: If the module doesn't contain a variable 'configuration`.
        TypeError: If the variable `configuration` is not of type `Configuration`.
    """
    if configuration_module is None:
        default_configuration_module_name = os.getenv(
            CONFIGURATION_MODULE_ENV_VARIABLE,
            CONFIGURATION_MODULE_DEFAULT,
        )
        configuration_module = default_configuration_module_name

    if configuration_module not in _configurations:
        try:
            _load_configuration_module(configuration_module)
        except ModuleNotFoundError:
            logger.warning(
                "No module found for config %s",
                configuration_module,
            )
            raise
    return _configurations[configuration_module]


def _load_configuration_module(module_name):
    if module_name in _configurations:
        raise RuntimeError("Already configured.")
    module = importlib.import_module(module_name)
    if not hasattr(module, 'configuration'):
        raise LookupError
    if not isinstance(module.configuration, Configuration):
        raise TypeError("'configuration' must be of type 'bandsaw.Configuration'.")
    configuration = module.configuration
    configuration.module_name = module_name
    _configurations[module_name] = configuration

    for extension in configuration.extensions:
        extension.on_init(configuration)
