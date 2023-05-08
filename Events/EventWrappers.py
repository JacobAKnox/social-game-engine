import functools
import logging
from typing import Any

logger = logging.getLogger(__name__)


def check_argument(name: str, type_: type = Any):
    def check_argument_wrapper(func):
        @functools.wraps(func)
        def wrapper_decorator(*args, **kwargs):
            if name not in kwargs:
                raise ValueError(f"kwarg {name} not provided to {func.__name__}")
            if type_ is not Any and not isinstance(kwargs[name], type_):
                raise ValueError(f"kwarg {name} provided to {func.__name__} is not of required type {type_.__name__}")
            value = func(*args, **kwargs)
            return value

        return wrapper_decorator

    return check_argument_wrapper
