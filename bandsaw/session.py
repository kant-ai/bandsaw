"""Contains classes for representing an advising session"""
import abc
import collections
import io
import json
import logging
import pathlib
import zipfile

from .config import get_configuration
from .distribution import get_distribution_archive
from .identifier import identifier_from_string
from .run import get_run_id
from .serialization import SerializableValue


logger = logging.getLogger(__name__)


class Attachment(abc.ABC):
    """
    Class that represents a single file that as been attached to a session.
    """

    @abc.abstractmethod
    def open(self):
        """
        Opens the attachment for reading.

        Returns:
            io.RawIOBase: binary stream for reading.
        """

    @property
    @abc.abstractmethod
    def size(self):
        """Return the size of the attachment in bytes"""


class _FileAttachment(Attachment):
    def __init__(self, path):
        self._path = path

    def open(self):
        return self._path.open('rb')

    @property
    def size(self):
        return self._path.stat().st_size


class _ZipAttachment(Attachment):
    def __init__(self, zip_file, path):
        self._zip_file = zip_file
        self._path = path

    def open(self):
        return self._zip_file.open(self._path)

    @property
    def size(self):
        return self._zip_file.getinfo(self._path).file_size


class Attachments(collections.abc.Mapping):
    """
    A mapping that contains attachments.

    Attachments can only be added, but neither deleted nor overwritten. Their names
    must be valid file names without directories.

    Attachments itself is a mapping class and can be used similar to a dictionary.
    When a new attachments is added, it must be path to an existing file, either as
    `str` or `pathlib.Path`. When an attachment is accessed, an object of type
    `Attachment` is returned, that gives access to the size of the attachment and
    allows to read its content.

    Examples:
        >>> attachments = Attachments()
        >>> attachments['my.attachment'] = '/path/to/file'
        >>> attachment = attachments['my.attachment']
        >>> attachment.size
        1234
        >>> attachment.open().readall()
        b'My binary file content.'

    """

    def __init__(self, zip_file=None):
        """
        Creates a new container for attachments.

        Args:
            zip_file (zipfile.ZipFile): An already existing zip file, which can be
                used for initializing with pre-existing attachments.
        """
        self._items = {}
        if zip_file is not None:
            self._add_attachments_from_zip(zip_file)

    def _add_attachments_from_zip(self, zip_file):
        for file_path in zip_file.namelist():
            if file_path[:12] == 'attachments/':
                attachment_name = file_path.split('/', 1)[1]
                self._items[attachment_name] = _ZipAttachment(zip_file, file_path)

    def store(self, zip_file):
        """
        Stores all attachments in a zip file.

        Args:
            zip_file (zipfile.ZipFile): The zip file where the attachments should be
                stored in.
        """
        for name, attachment in self._items.items():
            with attachment.open() as stream:
                zip_file.writestr('attachments/' + name, stream.read())

    def __setitem__(self, key, path):
        if key in self._items:
            raise KeyError(f"Attachment '{key}' does already exist")
        if isinstance(path, str):
            path = pathlib.Path(path)
        if not isinstance(path, pathlib.Path):
            raise TypeError("Invalid type for value, must be str or Path")
        if not path.exists():
            raise ValueError("File does not exist")
        if not path.is_file():
            raise ValueError("Path is not a file")
        self._items[key] = _FileAttachment(path)

    def __getitem__(self, key):
        return self._items[key]

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)


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
        execution (bandsaw.execution.Execution): The execution arguments for the task.
        context (bandsaw.context.Context): The context that can be used for advices
            to store state.
        result (bandsaw.result.Result): Result of the task if already computed.
            Otherwise, `None`.
        attachments (bandsaw.session.Attachments): A mapping of files that have been
            attached to the session.
        _configuration (bandsaw.config.Configuration): The configuration that is being
            used for advising this task.
    """

    # pylint: disable=too-many-instance-attributes
    # is reasonable in this case.

    def __init__(
        self,
        task=None,
        execution=None,
        configuration=None,
        advice_chain='default',
    ):
        """
        Create a new session.


        """
        self.task = task
        self.execution = execution
        self.context = {}
        self.result = None
        self.attachments = Attachments()
        self._configuration = configuration
        self._advice_chain = advice_chain
        self._moderator = None
        self._session_id = None
        self._temp_dir = None

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
            extension.on_before_advice(self.task, self.execution, self.context)

        self.proceed()

        if not self._moderator.is_finished:
            raise RuntimeError(
                f"Not all advice has been applied. "
                f"Misbehaving advice {self._moderator.current_advice}"
            )

        logger.debug("running extensions after advice")
        for extension in self._configuration.extensions:
            extension.on_after_advice(
                self.task, self.execution, self.context, self.result
            )
        return self.result

    @property
    def session_id(self):
        """The id of this session."""
        if self._session_id is None:
            if self.task is None or self.execution is None:
                raise ValueError("Incomplete session, missing task or execution.")
            self._session_id = identifier_from_string(
                ":".join(
                    [self.run_id, self.task.task_id, self.execution.execution_id],
                )
            )
        return self._session_id

    @property
    def serializer(self):
        """The serializer that can be used for serializing values."""
        return self._configuration.serializer

    @property
    def distribution_archive(self):
        """The DistributionArchive which can be used when transferring the session."""
        return get_distribution_archive(self._configuration)

    @property
    def run_id(self):
        """The run id of the workflow."""
        return get_run_id()

    @property
    def temp_dir(self):
        """
        Temporary directory where session specific files can be written to.

        This directory is meant for storing temporary files, that are used by the
        individual `Advice` instances. The directory is already created and will be
        automatically deleted with the end of the python interpreter, nonetheless,
        the advices writing files to the directory should if possible take care of
        removing them if no longer needed.

        Returns:
            pathlib.Path: Path to the temporary directory.
        """
        if self._temp_dir is None:
            self._temp_dir = self._configuration.temporary_directory / self.session_id
            self._temp_dir.mkdir(exist_ok=True)
        return self._temp_dir

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

        # We don't use with here, because we don't want to close the zip file
        # This allows the attachment's container, to access the attachments from the
        # archive
        archive = zipfile.ZipFile(stream, 'r')  # pylint: disable=consider-using-with

        session_json = json.loads(archive.read('session.json'))
        self._configuration = get_configuration(session_json['configuration'])
        self._advice_chain = session_json['advice_chain']
        self._session_id = session_json['session_id']

        serializer = self._configuration.serializer

        stream = io.BytesIO(archive.read('task.dat'))
        self.task = serializer.deserialize(stream)

        stream = io.BytesIO(archive.read('execution.dat'))
        self.execution = serializer.deserialize(stream)

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

        self.attachments = Attachments(archive)

    def _store_as_zip(self, stream):
        serializer = self._configuration.serializer

        with zipfile.ZipFile(stream, 'w') as archive:
            session_json = json.dumps(
                {
                    'configuration': self._configuration.module_name,
                    'advice_chain': self._advice_chain,
                    'session_id': self.session_id,
                }
            )
            archive.writestr('session.json', session_json)

            stream = io.BytesIO()
            serializer.serialize(self.task, stream)
            archive.writestr('task.dat', stream.getvalue())

            stream = io.BytesIO()
            serializer.serialize(self.execution, stream)
            archive.writestr('execution.dat', stream.getvalue())

            stream = io.BytesIO()
            serializer.serialize(self.context, stream)
            archive.writestr('context.dat', stream.getvalue())

            stream = io.BytesIO()
            serializer.serialize(self.result, stream)
            archive.writestr('result.dat', stream.getvalue())

            stream = io.BytesIO()
            serializer.serialize(self._moderator, stream)
            archive.writestr('moderator.dat', stream.getvalue())

            self.attachments.store(archive)


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
    others, will have its `after()` method called last.

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
            result = session.task.execute(session.execution)
            self.task_called = True
            session.conclude(result)

        elif self.after_called < len(self.advice_chain):
            advice_index = -1 - self.after_called
            advice = self.advice_chain[advice_index]
            self.after_called += 1
            advice.after(session)

        elif self.after_called == len(self.advice_chain):
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
            'is_finished': self._is_finished,
        }

    def __getstate__(self):
        return self.serialized()

    def __setstate__(self, values):
        self.before_called = values['before_called']
        self.after_called = values['after_called']
        self.task_called = values['task_called']
        self._is_finished = values['is_finished']

    @classmethod
    def deserialize(cls, values):
        queue = _Moderator()
        queue.before_called = values['before_called']
        queue.after_called = values['after_called']
        queue.task_called = values['task_called']
        queue._is_finished = values['is_finished']
        return queue
