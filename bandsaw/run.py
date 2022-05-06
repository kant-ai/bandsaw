"""Functions for managing the run id."""
import logging
import os
import sys
import uuid

from bandsaw.datetime import current_timestamp
from bandsaw.user import get_current_username


logger = logging.getLogger(__name__)


_RUN_ID = None
_RUN = None


class Run:
    """
    A Run represents a single run of a workflow.

    It contains additional meta data about the run, like e.g. the timestamp the run was
    started or other useful data. Once set, the run doesn't change.
    """

    #  pylint: disable=too-many-arguments

    def __init__(
        self,
        run_id,
        start_date=None,
        user=None,
        command=None,
        env=None,
        meta=None,
    ):
        self.run_id = run_id
        self.start_date = start_date or current_timestamp()
        self.user = user or get_current_username()
        self.command = command or sys.argv
        self.env = env or dict(os.environ)
        self.meta = meta or {}

    def to_json(self):
        """
        Returns a JSON representation for serializing the run.

        Returns:
            dict: A dictionary with the JSON values.
        """
        return {
            'id': self.run_id,
            'start_date': self.start_date,
            'user': self.user,
            'command': self.command,
            'env': self.env,
            'meta': self.meta,
        }

    @classmethod
    def from_json(cls, run_json):
        """
        Recreate a Run instance from its JSON representation.

        Args:
            run_json:

        Returns:
            Run: The recreated Run instance.
        """
        return Run(
            run_json['id'],
            start_date=run_json['start_date'],
            user=run_json['user'],
            command=run_json['command'],
            env=run_json['env'],
            meta=run_json['meta'],
        )


def get_run():
    """
    Returns the run.

    The run contains information about the environment of a specific
    run of a workflow.

    Returns:
        bandsaw.run.Run: The single run.
    """
    global _RUN  # pylint: disable=global-statement
    if _RUN is None:
        _RUN = Run(get_run_id())
    return _RUN


def get_run_id():
    """
    Returns the run id.

    The run id is a unique identifier that is specific to an individual run of a
    workflow. It stays the same across all task executions and can be used for
    tracking metrics and differentiating between different runs of the same workflow
    where task_id and run_id stay the same.

    Returns:
        str: The unique run id.
    """
    if _RUN_ID is None:
        set_run_id(str(uuid.uuid1()))
    return _RUN_ID


def set_run_id(run_id):
    """
    Sets the run id.

    Setting the run id explicitly is usually not necessary. The function is mainly
    used when task executions are run in a different process to make sure the run id
    is consistent with the spawning process, but it can be used e.g. if an external
    system provides a unique identifier for a specific workflow run.

    When `set_run_id(run_id)` is being used, it must be run before the first tasks
    are actually defined.

    Raises:
        RuntimeError: If the run id was already set before.
    """
    global _RUN_ID  # pylint: disable=global-statement
    if _RUN_ID is not None:
        logger.error("run_id already set to %s when trying to set again", _RUN_ID)
        raise RuntimeError("Run ID was already set")
    logger.info("Set run_id to %s", run_id)
    _RUN_ID = run_id
