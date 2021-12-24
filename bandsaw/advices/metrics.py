"""Contains an `Advice` implementation which gathers metrics."""
import logging
import pathlib

import multimeter

from ..advice import Advice


logger = logging.getLogger(__name__)


class MetricsAdvice(Advice):
    """An Advice which gathers metrics.

    Underneath this advice uses the python `multimeter` library for collecting the
    metrics.
    """

    def __init__(self, meter, directory=None, file_format=multimeter.JsonFormat()):
        """
        Creates a new MetricsAdvice that gathers metrics.

        Args:
            meter (multimeter.Multimeter): The Multimeter instance which is used for
                gathering the metrics.
            directory (str): Path to a directory, where the metrics are temporarily
                stored. If `None` or omitted, the session temporary directory is used.
            file_format (multimeter.FileFormat): File format that defines the format
                in which the gathered metrics are stored. Defaults to
                `multimeter.JsonFormat`.
        """
        self._multimeter = meter
        if directory is not None:
            self._directory = pathlib.Path(directory)
        else:
            self._directory = None
        self._file_format = file_format

    def before(self, session):
        tags = {
            'run_id': session.run_id,
            'task_id': session.task.task_id,
            'execution_id': session.execution.execution_id,
            'session_id': session.session_id,
        }
        advice_parameters = session.task.advice_parameters
        additional_tags = advice_parameters.get('metrics', {}).get('tags', {})
        tags.update(additional_tags)

        logger.info("Measurement id %s with tags %s", session.session_id, tags)
        measurement = self._multimeter.measure(session.session_id, **tags)
        session.context['metrics.measurement'] = measurement

        logger.debug("Measurement start")
        measurement.start()
        session.proceed()

    def after(self, session):
        measurement = session.context.pop('metrics.measurement')
        logger.debug("Measurement end")
        measurement.end()

        directory = self._directory or session.temp_dir
        storage = multimeter.FileStorage(directory, self._file_format)
        storage.store(measurement.result)
        metrics_file_name = measurement.identifier + self._file_format.extension
        metrics_attachment_name = 'metrics' + self._file_format.extension
        session.attachments[metrics_attachment_name] = directory / metrics_file_name
        session.proceed()
