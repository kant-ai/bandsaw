"""Contains classes for representing an advising session"""
import io
import json
import logging
import tempfile
import zipfile

from .config import get_configuration
from .distribution import create_distribution_archive
from .serialization import SerializableValue


logger = logging.getLogger(__name__)


class Session:
    """
    Class that handles the advising of an execution.

    A `Session` object is given to the individual advices that are called to advise
    the execution. By calling the appropriate methods like `def proceed(self)` to
    continue or `conclude()` to end with a result, the advices can influence the final
    result.
    Additionally, the session provides access to the `context`, which allows advices
    to keep state, the `execution` that is advised, the `configuration` that is used
    for advising and the `result` of the execution.

    Attributes:
        task (bandsaw.tasks.Task): The task that is executed.
        run (bandsaw.run.Run): The run definition for the task.
        context (bandsaw.context.Context): The context that can be used for advices
            to store state.
        result (bandsaw.result.Result): Result of the task if already computed.
            Otherwise `None`.
        _configuration (bandsaw.config.Configuration): The configuration that is being
            used for advising this task.
    """

    def __init__(
        self,
        task=None,
        run=None,
        configuration=None,
        advice_chain='default',
    ):
        """
        Create a new session.


        """
        self.task = task
        self.run = run
        self.context = {}
        self.result = None
        self._configuration = configuration
        self._advice_chain = advice_chain
        self._moderator = None

    def initiate(self):
        """
        Start the process of advising an execution.

        Returns:
            bandsaw.result.Result: The final result of the execution after all
                advices.
        """

        self._moderator = _Moderator(
            self._configuration.get_advice_chain(self._advice_chain)
        )

        logger.debug("running extensions before advice")
        for extension in self._configuration.extensions:
            extension.on_before_advice(self.task, self.run, self.context)

        self.proceed()

        if not self._moderator.is_finished:
            raise RuntimeError(
                f"Not all advice has been applied. "
                f"Misbehaving advice {self._moderator.current_advice}"
            )

        logger.debug("running extensions after advice")
        for extension in self._configuration.extensions:
            extension.on_after_advice(self.task, self.run, self.context, self.result)
        return self.result

    @property
    def serializer(self):
        """The serializer that can be used for serializing values."""
        return self._configuration.serializer

    @property
    def distribution_archive_path(self):
        """The serializer that can be used for serializing values."""
        runner_path = tempfile.mkstemp(suffix='.pyz', prefix='distribution')[1]
        create_distribution_archive(
            runner_path,
            modules=[
                '__main__',
                self._configuration.module_name,
                *self._configuration.distribution_modules,
            ],
        )
        return runner_path

    def proceed(self):
        """
        Continue the process of advising with the next advice.
        """
        self._moderator.next(self)

    def conclude(self, result):
        """
        Conclude the process of advising with a `Result`.

        This can be used in two cases:

        1. Concluding BEFORE the task was actually executed. This will skip all
           subsequent advices defined later in the advice chain and will skip the
           task execution. The given `result` will then be used as preliminary result.
           All advices that are defined before the calling advice in the advice chain
           will still be called with there `after(session)` method.

        2. Concluding AFTER the task was actually executed. This will just change the
           `result` of the session and continue will all following advices.

        Args:
            result (bandsaw.result.Result): The result to conclude with.
        """
        self.result = result
        self._moderator.skip(self)

    def save(self, stream):
        """
        Suspend the session to be resumed later or elsewhere.
        """
        self._store_as_zip(stream)

    def restore(self, stream):
        """
        Resume a prior suspended session.
        """
        self._load_from_zip(stream)
        return self

    def _load_from_zip(self, stream):

        with zipfile.ZipFile(stream, 'r') as archive:

            session_json = json.loads(archive.read('session.json'))
            self._configuration = get_configuration(session_json['configuration'])
            self._advice_chain = session_json['advice_chain']

            serializer = self._configuration.serializer

            stream = io.BytesIO(archive.read('task.dat'))
            self.task = serializer.deserialize(stream)

            stream = io.BytesIO(archive.read('run.dat'))
            self.run = serializer.deserialize(stream)

            stream = io.BytesIO(archive.read('context.dat'))
            self.context = serializer.deserialize(stream)

            stream = io.BytesIO(archive.read('result.dat'))
            self.result = serializer.deserialize(stream)

            stream = io.BytesIO(archive.read('moderator.dat'))
            self._moderator = serializer.deserialize(stream)
            if self._moderator is not None:
                self._moderator.advice_chain = self._configuration.get_advice_chain(
                    self._advice_chain
                )

    def _store_as_zip(self, stream):
        serializer = self._configuration.serializer

        with zipfile.ZipFile(stream, 'w') as archive:
            session_json = json.dumps(
                {
                    'configuration': self._configuration.module_name,
                    'advice_chain': self._advice_chain,
                }
            )
            archive.writestr('session.json', session_json)

            stream = io.BytesIO()
            serializer.serialize(self.task, stream)
            archive.writestr('task.dat', stream.getvalue())

            stream = io.BytesIO()
            serializer.serialize(self.run, stream)
            archive.writestr('run.dat', stream.getvalue())

            stream = io.BytesIO()
            serializer.serialize(self.context, stream)
            archive.writestr('context.dat', stream.getvalue())

            stream = io.BytesIO()
            serializer.serialize(self.result, stream)
            archive.writestr('result.dat', stream.getvalue())

            stream = io.BytesIO()
            serializer.serialize(self._moderator, stream)
            archive.writestr('moderator.dat', stream.getvalue())


class _Moderator(SerializableValue):
    """
    Class that keeps track which advices were already applied and which will be
    applied next.

    The moderator is responsible for calling the individual advices and the task in
    the correct order. Each call to the moderator's `next(session)` method,
    progresses by one step. First all `before()` methods of the advices are called in
    the order, that the advices are defined in the `advice_chain`. Then the task is
    executed and at last we apply the `after()` in the reversed order of the advices.
    This means that the first advice, whose `before()` method was called before all
    others, will has its `after()` method called last.

    Attributes:
        before_called (int): The number of advices where `before()` was called.
        after_called (int): The number of advices where `after()` was called.
        task_called (boolean): If the task was already called.
        advice_chain (List[bandsaw.advice.Advice]): The list of the advices that need
            to be applied.
    """

    def __init__(self, advice_chain=None):
        self.advice_chain = advice_chain
        self.before_called = 0
        self.after_called = 0
        self.task_called = False
        self._is_finished = False

    def next(self, session):
        """Apply either next advice or execute the task execution."""

        if self._is_finished:
            raise RuntimeError("Session already finished advising.")

        if self.before_called < len(self.advice_chain):
            advice = self.advice_chain[self.before_called]
            self.before_called += 1
            advice.before(session)

        elif not self.task_called:
            result = session.task.execute_run(session.run)
            self.task_called = True
            session.conclude(result)

        elif self.after_called < len(self.advice_chain):
            advice_index = -1 - self.after_called
            advice = self.advice_chain[advice_index]
            self.after_called += 1
            advice.after(session)

        if self.after_called == len(self.advice_chain):
            self._is_finished = True

    def skip(self, session):
        """
        Skip the remaining advices that follow the current advice in the advice chain
        """
        if not self.task_called:
            current_advice = self.advice_chain[self.before_called - 1]
            logger.info("Skip advice after %s", current_advice)

            self.after_called = len(self.advice_chain) - self.before_called + 1
            self.before_called = len(self.advice_chain)
            self.task_called = True

            advice_index = -1 - self.after_called
            if -advice_index <= len(self.advice_chain):
                next_advice = self.advice_chain[advice_index]
                logger.info("Next advice %s", next_advice)

        self.next(session)

    @property
    def current_advice(self):
        """
        The current advice that needs to be applied.

        Returns:
            Advice: The advice that needs to be applied, or `None`, if all advices
                have been applied and the moderator `is_finished`.
        """
        if self.advice_chain:
            if not self.task_called:
                return self.advice_chain[self.before_called - 1]

            if not self.is_finished:
                advice_index = -self.after_called
                return self.advice_chain[advice_index]
        return None

    @property
    def is_finished(self):
        """
        Tells if the moderator has called all advices.

        Returns:
            boolean: `True` if all advices have been applied and the task was called,
                otherwise `False`.
        """
        return self._is_finished

    def serialized(self):
        return {
            'before_called': self.before_called,
            'after_called': self.after_called,
            'task_called': self.task_called,
        }

    @classmethod
    def deserialize(cls, values):
        queue = _Moderator()
        queue.before_called = values['before_called']
        queue.after_called = values['after_called']
        queue.task_called = values['task_called']
        return queue
