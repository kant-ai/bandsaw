import unittest.mock

from bandsaw.advices.log import LoggingAdvice


class TestCachingAdvice(unittest.TestCase):

    def test_before_logs(self):
        with unittest.mock.patch('bandsaw.advices.log.logger') as logger_mock:
            advice = LoggingAdvice()
            session_mock = unittest.mock.MagicMock()

            advice.before(session_mock)

            session_mock.proceed.assert_called()
            logger_mock.info.assert_called()

    def test_after_logs(self):
        with unittest.mock.patch('bandsaw.advices.log.logger') as logger_mock:
            advice = LoggingAdvice()
            session_mock = unittest.mock.MagicMock()

            advice.after(session_mock)

            session_mock.proceed.assert_called()
            logger_mock.info.assert_called()


if __name__ == '__main__':
    unittest.main()
