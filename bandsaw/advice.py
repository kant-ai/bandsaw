"""Contains classes and functions for advising tasks."""
from .session import Session


def advise_task_with_chain(task, run, configuration, advice_chain='default'):
    """
    Executes an `Task` with additional advices.

    Args:
        task (bandsaw.tasks.Task): The task to be executed.
        run (bandsaw.run.Run): The run definition for the task.
        configuration (bandsaw.config.Configuration): The configuration which should
            be used during advising.
        advice_chain (str): The name of the advice chain which contains the additional
            advices to be applied to the task. Defaults to 'default'.

    Returns:
        bandsaw.result.Result: The result of the task execution.

    """
    session = Session(task, run, configuration, advice_chain)
    return session.initiate()


class Advice:
    """
    Interface that needs to be implemented by an advice.

    The interface is quite simple. One has to implement two different methods,
    `before(session)` and `after(session)`, that are called during the process of
    advising a task execution. Both take a single argument `session` which contains an
    instance of the class `Session`. This object allows the individual advices to
    influence the task execution by changing the way the task is being called or
    making changes to the result.
    """

    def before(self, session):  # pylint: disable=R0201 # no-self-use
        """
        Called before the task is actually executed.

        This methods allows the individual advice, to make changes to the way the
        task execution is later executed. In order to continue, the advice MUST either
        call `session.proceed()`, which will continue the process with the next
        advice in the advice chain, or call `session.conclude(result)` with a `Result`
        instance, which will skip the following advices and return without executing
        the task execution at all.

        The default implementation will just call `session.proceed()`.

        Args:
            session (bandsaw.session.Session): The session of the execution.
        """
        session.proceed()

    def after(self, session):  # pylint: disable=R0201 # no-self-use
        """
        Called after the task is actually executed.

        This methods allows the individual advice, to make changes to the result of
        the task execution. The result can be retrieved from the `session`.

        In order to continue, the advice MUST either call `session.proceed()`, which
        will continue the process with current `result` and the next advice in the
        advice chain, or call `session.conclude(result)` with a `Result` instance,
        which will set a different result and continue with it.

        The default implementation will just call `session.proceed()`.

        Args:
            session (bandsaw.session.Session): The session of the execution.
        """
        session.proceed()
