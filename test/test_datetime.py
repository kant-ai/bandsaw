import datetime
import sys
import unittest

from bandsaw.datetime import current_timestamp


class TestCurrentTimestamp(unittest.TestCase):

    @unittest.skipIf(sys.version_info.minor < 7, "Only supported in python >= 3.7")
    def test_timestamps_are_in_isoformat(self):
        timestamp = current_timestamp()
        datetime_value = datetime.datetime.fromisoformat(timestamp)
        self.assertIsInstance(datetime_value, datetime.datetime)


if __name__ == '__main__':
    unittest.main()
