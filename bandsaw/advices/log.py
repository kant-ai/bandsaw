"""Contains an `Advice` implementation which adds logging"""
import logging

from ..advice import Advice


logger = logging.getLogger(__name__)


class LoggingAdvice(Advice):
    """An Advice which adds additional logging"""

    def before(self, session):
        logger.info(
            "BEFORE %s:%s with context %s",
            session.task.task_id,
            session.execution.execution_id,
            session.context,
        )
        session.proceed()

    def after(self, session):
        logger.info(
            "AFTER %s:%s with context %s",
            session.task.task_id,
            session.execution.execution_id,
            session.context,
        )
        session.proceed()
