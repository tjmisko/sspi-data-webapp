from functools import wraps
import importlib
import pkgutil
from typing import Callable
dataset_registry = {}

def dataset(name: str):
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
        dataset_registry[name] = wrapper
        return wrapper
    return decorator

for _, modname, _ in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{modname}")
