"""date/time related utility functions"""
import datetime


def current_timestamp():
    """
    Returns a timestamp as string of the current time.

    Returns:
        str: Timestamp in ISO format with milliseconds in UTC.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    return timestamp.isoformat(timespec='milliseconds')


def datetime_from_timestamp(timestamp):
    """
    Parse a timestamp string to datetime.

    Args:
        timestamp (str): A timestamp as string.

    Returns:
        datetime.datetime: A datetime instance of the timestamp.
    """
    return datetime.datetime.fromisoformat(timestamp)
