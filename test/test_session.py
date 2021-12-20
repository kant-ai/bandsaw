import io
import pathlib
import pickle
import threading
import unittest
import unittest.mock
import zipfile

from bandsaw.advice import Advice
from bandsaw.config import Configuration
from bandsaw.extensions import Extension
from bandsaw.execution import Execution
from bandsaw.session import Attachment, Attachments, Session, _Moderator


class TestAttachments(unittest.TestCase):

    def setUp(self):
        self.attachments = Attachments()

    def test_attachments_is_empty_default(self):
        self.assertFalse(self.attachments)
        self.assertEqual(0, len(self.attachments))

    def test_attachments_can_be_used_as_mapping(self):
        self.attachments['my.item'] = __file__
        self.assertIsNotNone(self.attachments['my.item'])
        self.assertTrue(self.attachments)
        self.assertEqual(1, len(self.attachments))

    def test_attachments_can_be_paths(self):
        self.attachments['my.item'] = pathlib.Path(__file__)
        self.assertIsNotNone(self.attachments['my.item'])
        self.assertTrue(self.attachments)
        self.assertEqual(1, len(self.attachments))

    def test_attachments_can_be_iterated_over(self):
        self.attachments['my.item'] = __file__
        self.attachments['other.item'] = __file__
        iterator = iter(self.attachments)
        self.assertEqual('my.item', next(iterator))
        self.assertEqual('other.item', next(iterator))

    def test_attachments_values_are_attachments(self):
        self.attachments['my.item'] = __file__
        value = self.attachments['my.item']
        self.assertIsInstance(value, Attachment)

    def test_setting_attachments_must_be_paths_or_strings(self):
        with self.assertRaisesRegex(TypeError, "Invalid type for value"):
            self.attachments['my.item'] = 1

    def test_setting_attachments_path_must_exist(self):
        with self.assertRaisesRegex(ValueError, "File does not exist"):
            self.attachments['my.item'] = "not-existing"

    def test_setting_attachments_path_must_be_file(self):
        with self.assertRaisesRegex(ValueError, "Path is not a file"):
            self.attachments['my.item'] = pathlib.Path(__file__).parent

    def test_attachments_cant_be_overwritten(self):
        self.attachments['my.item'] = __file__
        with self.assertRaisesRegex(KeyError, "Attachment 'my.item' does already exist"):
            self.attachments['my.item'] = __file__

    def test_file_attachments_can_be_read(self):
        self.attachments['my.item'] = __file__
        with self.attachments['my.item'].open() as stream:
            self.assertEqual(b'import io\n', stream.readline())

    def test_file_attachments_can_return_file_size(self):
        self.attachments['my.item'] = __file__
        self.assertEqual(pathlib.Path(__file__).stat().st_size, self.attachments['my.item'].size)

    def test_attachments_can_be_initialized_from_zip_file(self):
        zip_file = zipfile.ZipFile(pathlib.Path(__file__).parent / 'attachments.zip')
        attachments = Attachments(zip_file)
        self.assertIn('test.txt', attachments)
        self.assertIn('other.log', attachments)
        self.assertNotIn('no.attachment', attachments)

    def test_zip_attachments_can_be_read(self):
        zip_file = zipfile.ZipFile(pathlib.Path(__file__).parent / 'attachments.zip')
        attachments = Attachments(zip_file)
        with attachments['test.txt'].open() as stream:
            self.assertEqual(b'My test.txt content.', stream.read())

    def test_zip_attachments_can_return_file_size(self):
        zip_file = zipfile.ZipFile(pathlib.Path(__file__).parent / 'attachments.zip')
        attachments = Attachments(zip_file)
        self.assertEqual(20, attachments['test.txt'].size)


class MyTask:

    def __init__(self, task_id='t'):
        self.task_id = task_id

    @staticmethod
    def execute(_):
        return True


class MySavingAdvice(Advice):

    def before(self, session):
        stream = io.BytesIO()
        session.save(stream)
        stream.seek(0)

        ### Here continue session somewhere else

        session.restore(stream)
        session.proceed()


def continue_session(stream):
    new_session = Session()
    new_session.restore(stream)
    new_session.proceed()


saved_session_with_result = None


class MyConcurrentAdvice(Advice):

    def before(self, session):
        session.context['before-thread-id'] = threading.current_thread().ident

        stream = io.BytesIO()
        session.save(stream)
        stream.seek(0)

        x = threading.Thread(target=continue_session, args=(stream,))
        x.start()
        x.join()

        # Continue in the original thread with the session
        # that contains the result
        global saved_session_with_result
        session.restore(saved_session_with_result)
        session.proceed()

    def after(self, session):
        # Called in the new thread, save the session again
        # and end the additional thread
        session.context['after-thread-id'] = threading.current_thread().ident
        global saved_session_with_result
        saved_session_with_result = io.BytesIO()
        session.save(saved_session_with_result)
        saved_session_with_result.seek(0)


class MyConcurrentTask:

    def __init__(self, task_id='t'):
        self.task_id = task_id

    @staticmethod
    def execute(_):
        return threading.current_thread().ident


class TestSession(unittest.TestCase):

    def setUp(self):
        self.config = Configuration()
        self.config.add_advice_chain(MySavingAdvice(), name='save')

    def test_session_contains_session_id(self):
        session = Session(MyTask(), Execution('1'), self.config)
        result = session.session_id
        self.assertIsNotNone(result)

    def test_session_id_is_cached(self):
        session = Session(MyTask(), Execution('1'), self.config)
        self.assertEqual(session.session_id, session.session_id)

    def test_session_id_changes_with_different_execution_id(self):
        session1 = Session(MyTask(), Execution('1'), self.config)
        session2 = Session(MyTask(), Execution('2'), self.config)
        self.assertNotEqual(session1.session_id, session2.session_id)

    def test_session_id_changes_with_different_task_id(self):
        session1 = Session(MyTask('1'), Execution('1'), self.config)
        session2 = Session(MyTask('2'), Execution('1'), self.config)
        self.assertNotEqual(session1.session_id, session2.session_id)

    def test_session_id_changes_with_different_run_id(self):
        with unittest.mock.patch("bandsaw.session.get_run_id", return_value='1'):
            session = Session(MyTask(), Execution('1'), self.config)
            session_id1 = session.session_id
        with unittest.mock.patch("bandsaw.session.get_run_id", return_value='2'):
            session = Session(MyTask(), Execution('1'), self.config)
            session_id2 = session.session_id
        self.assertNotEqual(session_id1, session_id2)

    def test_session_id_raises_with_incomplete_session(self):
        with self.assertRaisesRegex(ValueError, "Incomplete session"):
            session = Session(task=MyTask(), configuration=self.config)
            session.session_id
        with self.assertRaisesRegex(ValueError, "Incomplete session"):
            session = Session(execution=Execution('1'), configuration=self.config)
            session.session_id

    def test_empty_advice_returns_execution_result(self):
        session = Session(MyTask(), Execution('1'), self.config)
        result = session.initiate()
        self.assertTrue(result)

    def test_extensions_are_called(self):
        class MyExtension(Extension):
            def __init__(self):
                self.init_called = False
                self.before_called = False
                self.after_called = False

            def on_init(self, configuration):
                self.init_called = True

            def on_before_advice(self, task, execution, context):
                self.before_called = True

            def on_after_advice(self, task, execution, context, result):
                self.after_called = True

        extension = MyExtension()
        self.config.add_extension(extension)
        session = Session(MyTask(), Execution('1'), self.config)
        session.initiate()
        self.assertTrue(extension.before_called)
        self.assertTrue(extension.after_called)

    def test_no_proceeding_advice_raises_an_error(self):
        class NoProceedingAdvice(Advice):

            def before(self, session):
                pass

        self.config.add_advice_chain(NoProceedingAdvice(), name='no-proceeding')

        with self.assertRaisesRegex(RuntimeError, 'Not all advice.*NoProceedingAdvice'):
            session = Session(MyTask(), Execution('1'), self.config, 'no-proceeding')
            session.initiate()

    def test_double_proceeding_advice_raises_an_error(self):
        class DoubleProceedingAdvice(Advice):

            def before(self, session):
                session.proceed()
                session.proceed()

        self.config.add_advice_chain(DoubleProceedingAdvice(), name='double-proceeding')

        with self.assertRaisesRegex(RuntimeError, 'Session already finished'):
            session = Session(MyTask(), Execution('1'), self.config, 'double-proceeding')
            session.initiate()

    def test_advice_can_save_and_resume_session(self):
        with unittest.mock.patch("bandsaw.session.get_configuration", return_value=self.config):
            session = Session(MyTask(), Execution('1'), self.config, 'save')
            result = session.initiate()
            self.assertTrue(result)

    def test_session_restore_updates_configuration(self):
        with unittest.mock.patch("bandsaw.session.get_configuration", return_value=self.config):
            session = Session(MyTask(), Execution('1'), self.config)

            stream = io.BytesIO()
            session.save(stream)
            stream.seek(0)

            restored_session = Session().restore(stream)

            self.assertEqual(
                session._configuration.module_name,
                restored_session._configuration.module_name,
            )
            self.assertEqual(session._advice_chain, restored_session._advice_chain)
            self.assertEqual(session.context, restored_session.context)

    def test_session_restore_includes_attachments(self):
        with unittest.mock.patch("bandsaw.session.get_configuration", return_value=self.config):
            session = Session(MyTask(), Execution('1'), self.config)
            session.attachments['my.attachment'] = __file__

            stream = io.BytesIO()
            session.save(stream)
            stream.seek(0)

            restored_session = Session().restore(stream)

            self.assertEqual(
                session.attachments['my.attachment'].size,
                restored_session.attachments['my.attachment'].size,
            )
            self.assertEqual(
                session.attachments['my.attachment'].open().read(),
                restored_session.attachments['my.attachment'].open().read(),
            )

    def test_restored_session_has_same_session_id(self):
        with unittest.mock.patch("bandsaw.session.get_configuration", return_value=self.config):
            session = Session(MyTask(), Execution('1'), self.config)
            session.attachments['my.attachment'] = __file__

            stream = io.BytesIO()
            session.save(stream)
            stream.seek(0)

            restored_session = Session().restore(stream)

            self.assertEqual(
                session.session_id,
                restored_session.session_id,
            )

    def test_session_runs_parts_in_new_thread(self):
        self.config.add_advice_chain(MyConcurrentAdvice(), name='concurrent')

        with unittest.mock.patch("bandsaw.session.get_configuration", return_value=self.config):
            session = Session(MyConcurrentTask(), Execution('1'), self.config, 'concurrent')

            result = session.initiate()
            self.assertNotEqual(threading.current_thread().ident, result)

    def test_session_uses_serializer_from_configuration(self):
        session = Session(MyTask(), Execution('1'), self.config)

        serializer = session.serializer
        self.assertIs(serializer, self.config.serializer)

    def test_run_id_is_taken_from_get_run_id(self):
        with unittest.mock.patch("bandsaw.session.get_run_id", return_value='run-id'):
            session = Session(MyTask(), Execution('1'), self.config)
            run_id = session.run_id
            self.assertEqual(run_id, 'run-id')


class MyAdvice1(Advice):
    pass


class MyAdvice2(Advice):
    pass


class TestModerator(unittest.TestCase):

    def test_serialization(self):
        moderator = _Moderator()
        moderator.before_called = 2
        moderator.after_called = 1
        moderator.task_called = True

        serialized = moderator.serialized()
        deserialized = _Moderator.deserialize(serialized)

        self.assertEqual(moderator.before_called, deserialized.before_called)
        self.assertEqual(moderator.after_called, deserialized.after_called)
        self.assertEqual(moderator.task_called, deserialized.task_called)

    def test_current_advice_is_before(self):
        moderator = _Moderator([MyAdvice1(), MyAdvice2()])
        moderator.before_called = 1
        moderator.after_called = 0
        moderator.task_called = False

        self.assertIsInstance(moderator.current_advice, MyAdvice1)

        moderator.before_called = 2
        self.assertIsInstance(moderator.current_advice, MyAdvice2)

    def test_current_advice_is_after(self):
        moderator = _Moderator([MyAdvice1(), MyAdvice2()])
        moderator.before_called = 2
        moderator.after_called = 1
        moderator.task_called = True

        self.assertIsInstance(moderator.current_advice, MyAdvice2)

        moderator.after_called = 2
        self.assertIsInstance(moderator.current_advice, MyAdvice1)

    def test_current_advice_is_None_without_advices(self):
        moderator = _Moderator()
        self.assertIsNone(moderator.current_advice)

    def test_current_advice_is_None_when_finished(self):
        moderator = _Moderator([MyAdvice1()])
        moderator.before_called = 1
        moderator.after_called = 1
        moderator.task_called = True
        moderator._is_finished = True
        self.assertIsNone(moderator.current_advice)

    def test_pickling_keeps_all_state(self):
        moderator = _Moderator([MyAdvice1()])
        moderator.before_called = 1
        moderator.after_called = 1
        moderator.task_called = True
        moderator._is_finished = True
        pickled_moderator = pickle.dumps(moderator)
        unpickled_moderator = pickle.loads(pickled_moderator)
        self.assertEqual(unpickled_moderator.before_called, 1)
        self.assertEqual(unpickled_moderator.after_called, 1)
        self.assertTrue(unpickled_moderator.task_called)
        self.assertTrue(unpickled_moderator._is_finished)


if __name__ == '__main__':
    unittest.main()
