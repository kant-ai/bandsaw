import json
import pathlib
import shutil
import tempfile
import unittest

import multimeter

from bandsaw.advices.metrics import MetricsAdvice
from bandsaw.config import Configuration
from bandsaw.execution import Execution
from bandsaw.session import Session
from bandsaw.tasks import Task


def task_function():
    pass


class TestMetricsAdvice(unittest.TestCase):

    def setUp(self):
        self.mm = multimeter.Multimeter(cycle_time=0.01)
        self.advice = MetricsAdvice(self.mm)
        task = Task.create_task(task_function, task_kwargs={
            'metrics': {'tags': {'my': 'tag'}},
        })
        task.task_id = 't'
        self.configuration = Configuration()
        self.configuration.add_advice_chain(self.advice)
        self.session = Session(task, Execution('e'), self.configuration)

    def tearDown(self):
        shutil.rmtree(self.session.temp_dir)

    def test_metrics_added_as_attachment(self):
        self.session.initiate()
        self.assertIn('metrics.json', self.session.attachments)

    def test_metrics_attachment_extension_depends_on_format(self):
        self.advice._file_format = multimeter.LineFormat()
        self.session.initiate()
        self.assertIn('metrics.line', self.session.attachments)

    def test_session_id_is_used_as_measurement_identifier(self):
        self.session.initiate()
        metrics = json.load(self.session.attachments['metrics.json'].open())
        self.assertEqual(self.session.session_id, metrics['identifier'])

    def test_ids_are_added_as_tags_to_result(self):
        self.session.initiate()
        metrics = json.load(self.session.attachments['metrics.json'].open())
        self.assertEqual(self.session.session_id, metrics['tags']['session_id'])
        self.assertEqual(self.session.run_id, metrics['tags']['run_id'])
        self.assertEqual(self.session.task.task_id, metrics['tags']['task_id'])
        self.assertEqual(self.session.execution.execution_id, metrics['tags']['execution_id'])

    def test_tags_from_task_kwargs_are_added(self):
        self.session.initiate()
        metrics = json.load(self.session.attachments['metrics.json'].open())
        self.assertEqual('tag', metrics['tags']['my'])

    def test_directory_for_metrics_can_be_configured(self):
        result_dir = pathlib.Path(tempfile.mkdtemp())
        try:
            advice = MetricsAdvice(self.mm, directory=result_dir)
            self.configuration.add_advice_chain(advice)

            self.session.initiate()

            metrics_path = result_dir / (self.session.session_id + '.json')
            self.assertTrue(metrics_path.exists())
            self.assertTrue(metrics_path.is_file())
        finally:
            shutil.rmtree(result_dir)


if __name__ == '__main__':
    unittest.main()
