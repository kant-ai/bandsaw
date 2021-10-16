"""Utility functions for handling python modules."""
import importlib
import os.path
import sys


def object_as_import(obj):
    """
    Returns the name and module of an object, which can be used for importing it.

    Args:
        obj (object): An arbitrary Python object.

    Returns:
        Tuple(str, str): Returns a tuple of the object name and the module name in
            which the object is defined.

    Raises:
        ValueError: If `obj` doesn't have a name that can be directly imported, e.g.
            because it is defined within a local class.

    Note:
        If `obj` is defined within the `__main__` script, the function tries to
        determine a name for the `__main__` module, under which it could be imported
        from other scripts.

    """
    object_name = obj.__name__
    module_name = obj.__module__

    if module_name == '__main__':
        module_file_path = sys.modules['__main__'].__file__
        module_name = _guess_module_name_by_path(module_file_path, sys.path)

    if '<locals>' in obj.__qualname__:
        raise ValueError("Can't import local functions.")
    return object_name, module_name


def _guess_module_name_by_path(file_path, python_paths=None):
    base_file_path, ext = os.path.splitext(os.path.realpath(file_path))
    if ext != '.py':
        raise ValueError(f"Invalid python module file name {file_path}")

    for root in python_paths or sys.path:
        common_path = os.path.commonprefix([base_file_path, os.path.realpath(root)])
        if common_path == root:
            rel_path = os.path.relpath(base_file_path, root)
            return rel_path.replace(os.path.sep, '.')

    return None


def import_object(object_name, module_name):
    """
    Import a python object from a module.

    Args:
        object_name (str): The name under which the object is defined in the module.
        module_name (str): The name of the module from which the object should be
            imported.

    Returns:
        object: The python object defined under the name.

    Raises:
        AttributeError: If nothing is defined with name `object_name` in the
            referenced module.
        ModuleNotFoundError: If no module exists with the name `module_name`.
    """
    module = importlib.import_module(module_name)
    return getattr(module, object_name)


def get_loaded_module_name_by_path(file_path):
    """
    Determine the name of an already loaded module by its file path.

    Args:
        file_path (str): File path of the python file containing the module.

    Returns:
        str: The name of the module, or `None` if the file isn't loaded as a module.

    """
    real_path = os.path.realpath(file_path)
    for name, module in sys.modules.items():
        if hasattr(module, '__file__'):
            module_path = os.path.realpath(module.__file__)
            if module_path == real_path:
                return name
    return None
