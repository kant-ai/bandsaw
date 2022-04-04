"""Contains Advice that can cache task results in a local file system."""
import logging
import pathlib

from ..advice import Advice


logger = logging.getLogger(__name__)


class CachingAdvice(Advice):
    """
    Advice that caches results in a local filesystem.

    Attributes:
        directory (Path): The path to the directory where the results are cached.
    """

    def __init__(self, directory):
        self.directory = pathlib.Path(directory)
        logger.info("Caching artifacts in storage '%s'", self.directory)
        super().__init__()

    def before(self, session):
        artifact_id = session.task.task_id
        revision_id = session.execution.execution_id

        cache_item_path = self.directory / artifact_id / revision_id
        session.context['cache-item-path'] = str(cache_item_path)
        if (
            session.task.advice_parameters.get('cache', True)
            and cache_item_path.exists()
        ):
            logger.info("Using result from cache '%s'", cache_item_path)

            with open(cache_item_path, 'rb') as stream:
                result = session.serializer.deserialize(stream)
            session.conclude(result)
            return
        session.proceed()

    def after(self, session):
        if session.result.value:
            cache_item_path = pathlib.Path(session.context['cache-item-path'])
            if (
                session.task.advice_parameters.get('cache', True)
                and not cache_item_path.exists()
            ):
                cache_item_directory = cache_item_path.parent
                if not cache_item_directory.exists():
                    cache_item_directory.mkdir(parents=True)

                logger.info("Storing result in cache '%s'", cache_item_path)

                with open(cache_item_path, 'wb') as stream:
                    session.serializer.serialize(session.result, stream)
        session.proceed()
