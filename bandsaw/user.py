"""Contains functions related to users"""
import os
import pwd


def get_current_username():
    """
    Returns the name of the user which is currently running the python process.

    Returns:
        str: The name of the user on the local system.
    """
    return pwd.getpwuid(os.getuid())[0]
