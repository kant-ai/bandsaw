"""Infos about values, arguments and tasks"""


def value_info(value):
    """
    Information about a value.

    The information contains a string representation and a type name, but additional
    infos can be included as well.

    Args:
        value (Any): The value for which the infos should be returned.

    Returns:
        Dict[str,str]: A dictionary containing the infos about the value.
    """
    value_type = type(value)
    if isinstance(value, set):
        value = sorted(value)
    string_value = str(value)

    if len(string_value) > 100:
        string_value = string_value[:85] + '...' + string_value[-12:]

    info = {
        'type': value_type.__qualname__,
        'value': string_value,
    }
    if hasattr(value, '__len__'):
        info['size'] = str(len(value))

    if hasattr(value, 'info'):
        info.update(value.info())

    return info
