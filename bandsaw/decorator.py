"""Contains decorators that allow to define individual tasks"""
import io
import logging

from .advice import advise_task_with_chain
from .config import get_configuration
from .execution import Execution
from .identifier import identifier_from_bytes
from .tasks import Task


logger = logging.getLogger(__name__)


def task(*task_args, config=None, chain=None, **task_kwargs):
    """
    Decorator that is used to define a function as as task.

    The decorator can be used in two different ways, standalone:

    Example:
        >>> @task
        ... def my_task_function():
        ...      pass

    or with additional configuration.

    Example:
        >>> @task(config='my.config')
        ... def my_task_function():
        ...      pass


    Args:
        config (str): The name of the configuration module to use for this task.
            If not given, the default configuration is used.
        chain (str): The name of the advice chain to use for advising this task.
            If not given, 'default' is used.
        *task_args: Positional args given to the decorator OR the decorated function.
            If the decorator is used WITHOUT providing additional configuration,
            `task_args` contains a tuple with a single item that is the function to be
            used as a task. If there is additional configuration given, `task_args`
            contains the positional arguments of the call of the decorator.
        **task_kwargs: Keyword args given to the decorator.
            If the decorator is used WITHOUT providing additional configuration,
            `task_kwargs` is an empty dictionary. If there is additional configuration
            given, `task_kwargs`contains the keyword arguments of the call of the
            decorator.

    Returns:
        Callable: Returns a callable that wraps the decorated function.

    Raises:
        ModuleNotFoundError: If the configured configuration module does not exist.
        ValueError: If the specified advice chain does not exist.
        RuntimeError: If the task is configured with multiple positional arguments.
    """

    config_module = config
    configuration = get_configuration(config_module)

    chain_name = chain or 'default'
    chain = configuration.get_advice_chain(chain_name)
    if chain is None:
        raise ValueError(f"Unknown advice chain {chain_name}")

    def decorate_function(func):
        logger.info("Decorate function '%s'", func)

        logger.info("Creating task for function '%s'", func)
        the_task = Task.create_task(func, task_kwargs)

        def inner(*func_args, **func_kwargs):

            execution_id = _calculate_execution_id(
                func_args,
                func_kwargs,
                configuration.serializer,
            )
            execution = Execution(execution_id, func_args, func_kwargs)

            result = advise_task_with_chain(
                the_task,
                execution,
                configuration,
                chain_name,
            )
            if result.exception:
                raise result.exception
            return result.value

        inner.__wrapped__ = func
        inner.bandsaw_task = the_task
        inner.bandsaw_configuration = configuration
        return inner

    if len(task_args) == 1 and len(task_kwargs) == 0:
        return decorate_function(task_args[0])
    if len(task_args) == 0 and len(task_kwargs) > 0:
        return decorate_function
    # This shouldn't happen if the decorator is properly used.
    raise RuntimeError("Invalid 'task' decorator.")


def _calculate_execution_id(args, kwargs, serializer):
    """The unique id of an execution, derived from its arguments."""
    stream = io.BytesIO()
    value = (args, kwargs)
    serializer.serialize(value, stream)
    bytebuffer = stream.getvalue()
    return identifier_from_bytes(bytebuffer)
