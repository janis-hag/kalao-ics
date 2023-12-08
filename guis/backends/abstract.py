import time
from functools import wraps

from PySide6.QtCore import QObject


def emit(signal):
    def emit_(fun):
        @wraps(fun)
        def wrapper(self, *args, **kwargs):
            data = fun(self, *args, **kwargs)

            return getattr(self, signal).emit(data)

        return wrapper

    return emit_


def timeit(fun):
    @wraps(fun)
    def wrapper(self, *args, **kwargs):
        start = time.monotonic()

        data = fun(self, *args, **kwargs)

        end = time.monotonic()

        data.update({'metadata': {'duration': end - start}})

        return data

    return wrapper


def name_to_url(name):
    return '/' + name.replace('set_', '').replace('get_', '').replace('_', '/')


class AbstractBackend(QObject):
    pass
