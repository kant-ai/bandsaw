import io
import pickle
import threading
import unittest
import unittest.mock

from bandsaw.advice import Advice
from bandsaw.config import Configuration
from bandsaw.extensions import Extension
from bandsaw.execution import Execution
from bandsaw.session import Session, _Moderator


class MyTask:

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

    @staticmethod
    def execute(_):
        return threading.current_thread().ident


class TestSession(unittest.TestCase):

    def setUp(self):
        self.config = Configuration()
        self.config.add_advice_chain(MySavingAdvice(), name='save')

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
