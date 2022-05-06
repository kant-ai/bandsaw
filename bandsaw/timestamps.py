"""Collect timestamps for individual phases of a session."""
from bandsaw.datetime import current_timestamp
from bandsaw.extensions import Extension


class TimestampsExtension(Extension):
    """
    Extension that keeps timestamps for individual phases of executing session.

    These timestamps are stored within the session's context under the 'timestamps'
    key and are stored in iso-format for UTC:
      - 'timestamps.session_created': The time when the session was initially created.
      - 'timestamps.session_finished': The time when the session was finished.
      - 'timestamps.before_task': The time after applying all `before()` advices and
        before executing the task.
      - 'timestamps.before_task': The time before applying all `after()` advices and
        after executing the task.
    """

    def on_session_created(self, session):
        session.context['timestamps']['session_created'] = current_timestamp()

    def on_session_finished(self, session):
        session.context['timestamps']['session_finished'] = current_timestamp()

    def on_before_task_executed(self, session):
        session.context['timestamps']['before_task'] = current_timestamp()

    def on_after_task_executed(self, session):
        session.context['timestamps']['after_task'] = current_timestamp()
