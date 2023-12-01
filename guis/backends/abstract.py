import time
from functools import wraps

from PySide6.QtCore import QObject


class AbstractBackend(QObject):
    @staticmethod
    def timeit(data, signal):
        def timeit_(fun):
            @wraps(fun)
            def wrapper(self, *args, **kwargs):
                data_ = getattr(self, data)
                signal_ = getattr(self, signal)

                start = time.monotonic()

                ret = fun(self, data_, *args, **kwargs)

                end = time.monotonic()

                data_.update({'metadata': {'duration': end - start}})
                signal_.emit()

                return ret

            return wrapper

        return timeit_

    def consume_stream(self, data, stream_name, default=None):
        try:
            if not data[stream_name]['updated']:
                return default

            param = data[stream_name]['data']
        except KeyError:
            return default
        else:
            data[stream_name]['updated'] = False
            return param

    def consume_param(self, data, fps_name, param_name, default=None):
        try:
            if not data[fps_name][param_name]['updated']:
                return default

            param = data[fps_name][param_name]['value']
        except KeyError:
            return default
        else:
            data[fps_name][param_name]['updated'] = False
            return param
