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

    def on_before_advice(self, task, execution, context):
        """
        Called before bandsaw advises a task.

        Args:
            task (bandsaw.tasks.Task): The task which will be advised.
            execution (bandsaw.execution.Execution): The execution which contains the
                parametrization of the task.
            context (bandsaw.context.Context): The context which will be used during
                the advice. The context can be extended by the extension.
        """

    def on_after_advice(self, task, execution, context, result):
        """
        Called after bandsaw advises a task.

        Args:
            task (bandsaw.tasks.Task): The task which was advised.
            execution (bandsaw.execution.Execution): The execution which contains the
                parametrization of the task.
            context (bandsaw.context.Context): The context which was used during the
                advice.
            result (bandsaw.result.Result): The result of the call.
        """
