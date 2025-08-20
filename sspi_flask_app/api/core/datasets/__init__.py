from functools import wraps
import importlib
import pkgutil
from typing import Callable
dataset_collector_registry = {}

def dataset_collector(name: str):
    """
    Parameterized decorator: registers the function in the `datasets` dict.
    Usage:
        @dataset("foo")
        def load_foo(): ...
    Then: datasets["foo"] -> load_foo
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        dataset_collector_registry[name] = wrapper
        return wrapper
    return decorator

dataset_cleaner_registry = {}
def dataset_cleaner(name: str):
    """
    Parameterized decorator: registers the function in the `datasets` dict.
    Usage:
        @dataset("foo")
        def clean_foo(): ...
    Then: datasets["foo"] -> clean_foo
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        dataset_cleaner_registry[name] = wrapper
        return wrapper
    return decorator

# Recursively import all modules in this package and subdirectories
def import_submodules(package_name, package_path):
    """Recursively import all submodules of a package."""
    for importer, modname, ispkg in pkgutil.walk_packages(package_path, f"{package_name}."):
        if not ispkg:  # Only import actual modules, not packages
            try:
                importlib.import_module(modname)
            except ImportError as e:
                print(f"Warning: Could not import {modname}: {e}")

import_submodules(__name__, __path__)