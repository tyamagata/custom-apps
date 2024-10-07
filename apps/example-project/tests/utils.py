import functools

from mocket import Mocket, Mocketizer


def strict_mocketize(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        with Mocketizer(strict_mode=True):
            value = func(*args, **kwargs)
            Mocket.assert_fail_if_entries_not_served()
            return value

    return wrapper_decorator
