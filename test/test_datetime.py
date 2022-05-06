import datetime
import unittest

from bandsaw.datetime import current_timestamp, datetime_from_timestamp


class TestTimestamps(unittest.TestCase):

    def test_timestamps_are_in_isoformat(self):
        timestamp = current_timestamp()
        datetime_value = datetime.datetime.fromisoformat(timestamp)
        self.assertIsInstance(datetime_value, datetime.datetime)

    def test_datetime_from_timestamps(self):
        timestamp = '2022-04-05T01:02:03.456'
        datetime_value = datetime_from_timestamp(timestamp)
        self.assertIsInstance(datetime_value, datetime.datetime)
        self.assertEqual(datetime_value, datetime.datetime(2022, 4, 5, 1, 2, 3, 456000))


if __name__ == '__main__':
    unittest.main()
