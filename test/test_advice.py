import unittest

from bandsaw.advice import Advice, advise_task_with_chain
from bandsaw.config import Configuration
from bandsaw.result import Result
from bandsaw.execution import Execution


class TestAdviseFunctionWithChain(unittest.TestCase):

    def setUp(self):
        self.config = Configuration()

    def test_empty_advice_calls_function(self):
        called = False

        class MyTask:

            @staticmethod
            def execute(_):
                nonlocal called
                called = True

        advise_task_with_chain(MyTask(), Execution('1'), self.config)
        self.assertTrue(called)

    def test_return_value_is_Result(self):

        class MyTask:

            @staticmethod
            def execute(_):
                return Result(value=True)

        result = advise_task_with_chain(MyTask(), Execution('1'), self.config)
        self.assertIsInstance(result, Result)
        self.assertEqual(Result(value=True), result)

    def test_empty_advice_just_proceeds(self):
        called = False

        class EmptyAdvice(Advice):
            pass

        class MyTask:

            @staticmethod
            def execute(_):
                nonlocal called
                called = True

        self.config.add_advice_chain(EmptyAdvice())
        advise_task_with_chain(MyTask(), Execution('1'), self.config)
        self.assertTrue(called)

    def test_single_advice_before_after_are_called(self):
        before_called = False
        execution_called = False
        after_called = False

        class Advice1(Advice):

            def before(self_, session):
                nonlocal before_called
                self.assertFalse(execution_called, "Function already called")
                self.assertFalse(after_called, "After already called")
                before_called = True
                session.proceed()

            def after(self_, session):
                nonlocal after_called
                self.assertTrue(before_called, "Before not called")
                self.assertTrue(execution_called, "Function not called")
                after_called = True
                session.proceed()

        class MyTask:

            @staticmethod
            def execute(_):
                nonlocal execution_called
                self.assertTrue(before_called, "Before not called")
                self.assertFalse(after_called, "After already called")
                execution_called = True

        self.config.add_advice_chain(Advice1())
        advise_task_with_chain(MyTask(), Execution('1'), self.config)
        self.assertTrue(before_called)
        self.assertTrue(execution_called)
        self.assertTrue(after_called)

    def test_multiple_advices_before_after_are_called_in_the_correct_order(self):
        class MyAdvice(Advice):

            def __init__(self, value):
                self.value = value

            def before(self, session):
                session.execution.args[0].append(f'before {self.value}')
                session.proceed()

            def after(self, session):
                session.execution.args[0].append(f'after {self.value}')
                session.proceed()

        class MyTask:

            @staticmethod
            def execute(execution):
                execution.args[0].append('result')
                return Result(value=execution.args[0])

        self.config.add_advice_chain(MyAdvice(1), MyAdvice(2))
        result = advise_task_with_chain(MyTask(), Execution('1', [[]]), self.config)
        self.assertEqual(['before 1', 'before 2', 'result', 'after 2', 'after 1'], result.value)

    def test_first_advice_skips_all(self):

        class MyAdvice(Advice):

            def __init__(self, value):
                self.value = value

            def before(self, session):
                session.execution.args[0].append(f'before {self.value}')
                if self.value == 1:
                    session.conclude(Result(session.execution.args[0]))
                else:
                    session.proceed()

            def after(self, session):
                session.execution.args[0].append(f'after {self.value}')
                session.proceed()

        class MyTask:

            @staticmethod
            def execute(execution):
                execution.args[0].append('result')
                return execution.args[0]

        self.config.add_advice_chain(MyAdvice(1), MyAdvice(2), MyAdvice(3))
        result = advise_task_with_chain(
            MyTask(), Execution('1', [[]]), self.config,
        )
        self.assertEqual(['before 1'], result.value)

    def test_second_advice_skips_all_but_first_after(self):

        class MyAdvice(Advice):

            def __init__(self, value):
                self.value = value

            def before(self, session):
                session.execution.args[0].append(f'before {self.value}')
                if self.value == 2:
                    session.conclude(Result(session.execution.args[0]))
                else:
                    session.proceed()

            def after(self, session):
                session.execution.args[0].append(f'after {self.value}')
                session.proceed()

        class MyTask:

            @staticmethod
            def execute(execution):
                execution.args[0].append('result')
                return execution.args[0]

        self.config.add_advice_chain(MyAdvice(1), MyAdvice(2), MyAdvice(3))
        result = advise_task_with_chain(
            MyTask(), Execution('1', [[]]), self.config,
        )
        self.assertEqual(['before 1', 'before 2', 'after 1'], result.value)

    def test_last_advice_skips_only_own_after(self):

        class MyAdvice(Advice):

            def __init__(self, value):
                self.value = value

            def before(self, session):
                session.execution.args[0].append(f'before {self.value}')
                if self.value == 3:
                    session.conclude(Result(session.execution.args[0]))
                else:
                    session.proceed()

            def after(self, session):
                session.execution.args[0].append(f'after {self.value}')
                session.proceed()

        class MyTask:

            @staticmethod
            def execute(execution):
                execution.args[0].append('result')
                return execution.args[0]

        self.config.add_advice_chain(MyAdvice(1), MyAdvice(2), MyAdvice(3))
        result = advise_task_with_chain(
            MyTask(), Execution('1', [[]]), self.config,
        )
        self.assertEqual(['before 1', 'before 2', 'before 3', 'after 2', 'after 1'], result.value)


if __name__ == '__main__':
    unittest.main()
