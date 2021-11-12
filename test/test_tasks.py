import functools
import unittest

from bandsaw.tasks import Task, _FunctionTask


def free_function():
    return 'free-function'


def wrapper(func):
    @functools.wraps(func)
    def always_false(*args, **kwargs):
        return False
    return always_false


@wrapper
def wrapped_function():
    return True


class TestTask(unittest.TestCase):

    def test_create_task_handles_free_function(self):
        task = Task.create_task(free_function)
        self.assertEqual('8cecc949e9edc5293ffc', task.task_id)

        result = task._execute([], {})
        self.assertEqual('free-function', result)

        source = task.source
        self.assertEqual(source, "def free_function():\n    return 'free-function'\n")

        bytecode = task.bytecode
        self.assertEqual(bytecode, b'd\x01S\x00')

    def test_create_task_sets_task_kwargs(self):
        task = Task.create_task(free_function, {'my': 'kwargs'})

        self.assertEqual(task.kwargs, {'my': 'kwargs'})

    def test_free_function_tasks_can_be_serialized(self):
        task = Task.create_task(free_function)
        serialized = task.serialized()
        deserialized_task = _FunctionTask.deserialize(serialized)

        self.assertEqual(task.task_id, deserialized_task.task_id)
        self.assertIs(task.function, deserialized_task.function)

    def test_function_returns_wrapped_function(self):
        task = Task.create_task(wrapped_function)
        result = task.function()
        self.assertTrue(result)

    def test_create_task_handles_local_function(self):
        def local_function():
            return 'local-function'

        task = Task.create_task(local_function)
        self.assertEqual('71b50995b93786bb8d57', task.task_id)

        result = task._execute([], {})
        self.assertEqual('local-function', result)

        result = task.source
        self.assertEqual(result, "        def local_function():\n            return 'local-function'\n")

        with self.assertRaises(NotImplementedError):
            task.serialized()

        with self.assertRaises(NotImplementedError):
            type(task).deserialize(None)

    def test_create_task_raises_for_unknown_task_type(self):
        class MyClass:
            pass

        with self.assertRaisesRegex(TypeError, "Unsupported task object of type"):
            Task.create_task(MyClass)


if __name__ == '__main__':
    unittest.main()
