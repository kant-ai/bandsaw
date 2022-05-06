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
