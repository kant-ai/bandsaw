import io
import threading
import unittest
import unittest.mock

from bandsaw.advice import Advice
from bandsaw.config import Configuration
from bandsaw.extensions import Extension
from bandsaw.run import Run
from bandsaw.session import Session, _Moderator


class MyTask:

    @staticmethod
    def execute_run(_):
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
    def execute_run(_):
        return threading.current_thread().ident


class TestSession(unittest.TestCase):

    def setUp(self):
        self.config = Configuration()
        self.config.add_advice_chain(MySavingAdvice(), name='save')

    def test_empty_advice_returns_execution_result(self):
        session = Session(MyTask(), Run('1'), self.config)
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

            def on_before_advice(self, task, run, context):
                self.before_called = True

            def on_after_advice(self, task, run, context, result):
                self.after_called = True

        extension = MyExtension()
        self.config.add_extension(extension)
        session = Session(MyTask(), Run('1'), self.config)
        session.initiate()
        self.assertTrue(extension.before_called)
        self.assertTrue(extension.after_called)

    def test_no_proceeding_advice_raises_an_error(self):
        class NoProceedingAdvice(Advice):

            def before(self, session):
                pass

        self.config.add_advice_chain(NoProceedingAdvice(), name='no-proceeding')

        with self.assertRaisesRegex(RuntimeError, 'Not all advice.*NoProceedingAdvice'):
            session = Session(MyTask(), Run('1'), self.config, 'no-proceeding')
            session.initiate()

    def test_double_proceeding_advice_raises_an_error(self):
        class DoubleProceedingAdvice(Advice):

            def before(self, session):
                session.proceed()
                session.proceed()

        self.config.add_advice_chain(DoubleProceedingAdvice(), name='double-proceeding')

        with self.assertRaisesRegex(RuntimeError, 'Session already finished'):
            session = Session(MyTask(), Run('1'), self.config, 'double-proceeding')
            session.initiate()

    def test_advice_can_save_and_resume_session(self):
        with unittest.mock.patch("bandsaw.session.get_configuration", return_value=self.config):
            session = Session(MyTask(), Run('1'), self.config, 'save')
            result = session.initiate()
            self.assertTrue(result)

    def test_session_restore_updates_configuration(self):
        with unittest.mock.patch("bandsaw.session.get_configuration", return_value=self.config):
            session = Session(MyTask(), Run('1'), self.config)

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

    def test_session_run_parts_in_new_thread(self):
        self.config.add_advice_chain(MyConcurrentAdvice(), name='concurrent')

        with unittest.mock.patch("bandsaw.session.get_configuration", return_value=self.config):
            session = Session(MyConcurrentTask(), Run('1'), self.config, 'concurrent')

            result = session.initiate()
            self.assertNotEqual(threading.current_thread().ident, result)

    def test_session_uses_serializer_from_configuration(self):
        session = Session(MyTask(), Run('1'), self.config)

        serializer = session.serializer
        self.assertIs(serializer, self.config.serializer)


class MyAdvice1(Advice):
    pass


class MyAdvice2(Advice):
    pass


class TestModerator(unittest.TestCase):

    def test_serialization(self):
        queue = _Moderator()
        queue.before_called = 2
        queue.after_called = 1
        queue.task_called = True

        serialized = queue.serialized()
        deserialized = _Moderator.deserialize(serialized)

        self.assertEqual(queue.before_called, deserialized.before_called)
        self.assertEqual(queue.after_called, deserialized.after_called)
        self.assertEqual(queue.task_called, deserialized.task_called)

    def test_current_advice_is_before(self):
        queue = _Moderator([MyAdvice1(), MyAdvice2()])
        queue.before_called = 1
        queue.after_called = 0
        queue.task_called = False

        self.assertIsInstance(queue.current_advice, MyAdvice1)

        queue.before_called = 2
        self.assertIsInstance(queue.current_advice, MyAdvice2)

    def test_current_advice_is_after(self):
        queue = _Moderator([MyAdvice1(), MyAdvice2()])
        queue.before_called = 2
        queue.after_called = 1
        queue.task_called = True

        self.assertIsInstance(queue.current_advice, MyAdvice2)

        queue.after_called = 2
        self.assertIsInstance(queue.current_advice, MyAdvice1)

    def test_current_advice_is_None_without_advices(self):
        queue = _Moderator()
        self.assertIsNone(queue.current_advice)

    def test_current_advice_is_None_when_finished(self):
        queue = _Moderator([MyAdvice1()])
        queue.before_called = 1
        queue.after_called = 1
        queue.task_called = True
        queue._is_finished = True
        self.assertIsNone(queue.current_advice)


if __name__ == '__main__':
    unittest.main()
