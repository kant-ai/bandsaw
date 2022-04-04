"""Contains an API for extensions that can be used in bandsaw"""


class Extension:
    """
    Class that defines the interface of extensions.

    An extension can define different callbacks that are called by bandsaw and allows
    to extend some existing functionality (e.g. by setting additional values in a
    context before it is handled by all advices) or integrate other systems.
    Other than `Advice`, an `Extension` is globally defined in a config and therefore
    applies to all tasks.
    """

    def on_init(self, configuration):
        """
        Called when a bandsaw configuration has been initialized.

        Args:
            configuration (bandsaw.config.Configuration): The configuration object
                which contains the config that has been loaded.
        """

    def on_session_created(self, session):
        """
        Called before bandsaw advises a task.

        This is called before any advice is applied.

        Args:
            session (bandsaw.session.Session): The new session.
        """

    def on_session_finished(self, session):
        """
        Called after bandsaw advised a task.

        This is called after all advices have been applied and the final result is
        available.

        Args:
            session (bandsaw.session.Session): The session.
        """

    def on_before_task_executed(self, session):
        """
        Called bandsaw executes the task of a session.

        This is called after the `before()` advices are applied, but before the
        actual task is executed.

        Args:
            session (bandsaw.session.Session): The new session.
        """

    def on_after_task_executed(self, session):
        """
        Called after bandsaw has executed the task of a session.

        This is called after a task was executed, but before all `after()` advices
        are applied.

        Args:
            session (bandsaw.session.Session): The session.
        """
