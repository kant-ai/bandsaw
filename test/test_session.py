import io
import threading
import unittest

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
        final_session = Session()
        final_session.restore(saved_session_with_result)
        final_session.proceed()

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


configuration = Configuration()
configuration.add_advice_chain(MySavingAdvice(), name='save')
configuration.add_advice_chain(MyConcurrentAdvice(), name='concurrent')
configuration.add_extension(extension)


class TestSession(unittest.TestCase):

    def test_empty_advice_returns_execution_result(self):
        session = Session(MyTask(), Run('1'), configuration)
        result = session.initiate()
        self.assertTrue(result)

    def test_extensions_are_called(self):
        global extension
        session = Session(MyTask(), Run('1'), configuration)
        session.initiate()
        self.assertTrue(extension.before_called)
        self.assertTrue(extension.after_called)

    def test_advice_can_save_and_resume_session(self):
        session = Session(MyTask(), Run('1'), configuration, 'save')
        result = session.initiate()
        self.assertTrue(result)

    def test_session_restore_updates_configuration(self):
        session = Session(MyTask(), Run('1'), configuration)

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
        session = Session(MyConcurrentTask(), Run('1'), configuration, 'concurrent')

        result = session.initiate()
        self.assertNotEqual(threading.current_thread().ident, result)

    def test_session_uses_serializer_from_configuration(self):
        session = Session(MyConcurrentTask(), Run('1'), configuration, 'concurrent')

        serializer = session.serializer
        self.assertIs(serializer, configuration.serializer)


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


if __name__ == '__main__':
    unittest.main()
