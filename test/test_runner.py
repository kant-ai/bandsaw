import pathlib
import tempfile
import unittest.mock

from bandsaw.runner import main


class TestMain(unittest.TestCase):

    def setUp(self):
        self.input = pathlib.Path(tempfile.mkstemp()[1])
        self.output = pathlib.Path(tempfile.mkstemp()[1])

    def tearDown(self):
        self.input.unlink()
        self.output.unlink()

    @unittest.mock.patch('bandsaw.runner.Session')
    def test_main(self, session_mock):
        main(args=[
            '--input',
            str(self.input),
            '--output',
            str(self.output),
        ])


if __name__ == '__main__':
    unittest.main()
