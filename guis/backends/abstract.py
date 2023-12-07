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


class AbstractBackend(QObject):
    def consume_stream(self, data, stream_name, default=None):
        try:
            param = data[stream_name]['data']
        except KeyError:
            return default
        else:
            data[stream_name]['updated'] = False
            return param

    def consume_param(self, data, fps_name, param_name, default=None):
        try:
            param = data[fps_name][param_name]['value']
        except KeyError:
            return default
        else:
            data[fps_name][param_name]['updated'] = False
            return param

    def consume_plc(self, data, key, default=None):
        try:
            return data['plc'][key]
        except KeyError:
            return default

    def consume_service(self, data, key, default=None):
        try:
            return data['services'][key]
        except KeyError:
            return default