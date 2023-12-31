import pathlib
import shutil
import tempfile
import unittest

from bandsaw.advices.cache import CachingAdvice
from bandsaw.config import Configuration
from bandsaw.context import Context
from bandsaw.result import Result
from bandsaw.serialization.json import JsonSerializer
from bandsaw.session import Session
from bandsaw.tasks import Task
from bandsaw.execution import Execution


def task_function():
    pass


class TestCachingAdvice(unittest.TestCase):

    def setUp(self):
        self.configuration = Configuration()
        self.configuration.set_serializer(JsonSerializer())
        self.cache_dir = pathlib.Path(tempfile.mkdtemp())
        self.advice = CachingAdvice(self.cache_dir)
        task = Task.create_task(task_function)
        task.task_id = 't'
        self.session = Session(task, Execution('r'), self.configuration)
        self.session.proceed = lambda: None

    def tearDown(self):
        shutil.rmtree(self.cache_dir)

    def test_after_stores_result(self):
        cache_item_path = self.cache_dir / 't' / 'r'
        self.assertFalse(cache_item_path.exists())
        self.assertFalse(cache_item_path.is_file())

        self.advice.before(self.session)
        self.session.result = Result(value='My result')
        self.advice.after(self.session)

        self.assertTrue(cache_item_path.exists())
        self.assertTrue(cache_item_path.is_file())
        stored_result = self.session.serializer.deserialize(cache_item_path.open('rb'))
        self.assertEqual(Result(value="My result"), stored_result)

    def test_exceptions_in_results_are_not_cached(self):
        cache_item_path = self.cache_dir / 't' / 'r'
        self.assertFalse(cache_item_path.exists())
        self.assertFalse(cache_item_path.is_file())

        self.advice.before(self.session)
        self.session.result = Result(exception=Exception('error'))
        self.advice.after(self.session)

        self.assertFalse(cache_item_path.exists())

    def test_dont_store_again_if_exists(self):
        cache_item_path = self.cache_dir / 't' / 'r'
        self.assertFalse(cache_item_path.exists())
        self.assertFalse(cache_item_path.is_file())

        self.advice.before(self.session)
        self.session.result = Result(value='My result')
        self.advice.after(self.session)

        self.session.result = Result(value='My other result')
        self.advice.after(self.session)

        self.assertTrue(cache_item_path.exists())
        self.assertTrue(cache_item_path.is_file())
        stored_result = self.session.serializer.deserialize(cache_item_path.open('rb'))
        self.assertEqual(Result(value="My result"), stored_result)

    def test_dont_store_if_cache_is_disabled(self):
        task = Task.create_task(task_function, {'cache': False})
        task.task_id = 't'
        self.session = Session(task, Execution('r'), self.configuration)
        self.session.proceed = lambda: None

        cache_item_path = self.cache_dir / 't' / 'r'
        self.assertFalse(cache_item_path.exists())
        self.assertFalse(cache_item_path.is_file())

        self.advice.before(self.session)
        self.session.result = Result(value='My result')
        self.advice.after(self.session)

        self.assertFalse(cache_item_path.exists())

    def test_dont_create_cache_directory_again_if_exists(self):
        cache_item_path = self.cache_dir / 't' / 'r'
        self.assertFalse(cache_item_path.exists())
        self.assertFalse(cache_item_path.is_file())

        self.advice.before(self.session)
        self.session.result = Result(value='My result')
        self.advice.after(self.session)

        cache_task_path = self.cache_dir / 't'
        cache_execution_path = cache_task_path / 's'
        self.assertTrue(cache_task_path.exists())
        self.assertTrue(cache_task_path.is_dir())
        self.assertFalse(cache_execution_path.exists())

        self.session.execution = Execution('s')
        self.session.context = Context()

        self.advice.before(self.session)
        self.session.result = Result(value='My other result')
        self.advice.after(self.session)

        self.assertTrue(cache_execution_path.exists())
        self.assertTrue(cache_execution_path.is_file())

    def test_result_is_reused_from_existing_cache_item(self):
        concluded = False

        def conclude_check(self, result):
            self.result = result
            nonlocal concluded
            concluded = True

        # Bind the new conclude method to session object
        self.session.conclude = conclude_check.__get__(self.session, Session)

        cache_item_path = self.cache_dir / 't' / 'r'
        cache_item_path.parent.mkdir()
        cache_item_path.open('w').write('"My old result"')

        self.advice.before(self.session)

        self.assertEqual(self.session.result, 'My old result')
        self.assertTrue(concluded)


if __name__ == '__main__':
    unittest.main()
