import time
from datetime import datetime, timezone
from functools import wraps

from PySide6.QtCore import QObject, Signal


def emit(fun):
    @wraps(fun)
    def wrapper(self, *args, **kwargs):
        data = fun(self, *args, **kwargs)

        getattr(self, fun.__name__ + '_updated').emit(data)

        return data

    return wrapper


def timeit(fun):
    @wraps(fun)
    def wrapper(self, *args, **kwargs):
        start = time.monotonic()

        data = fun(self, *args, **kwargs)

        end = time.monotonic()

        data['metadata'] = {
            'duration': end - start,
            'timestamp': datetime.now(timezone.utc)
        }

        return data

    return wrapper


def name_to_url(name):
    return '/' + name.replace('_', '/')


class AbstractBackend(QObject):
    streams_all_updated = Signal(object)
    camera_image_updated = Signal(object)
    all_updated = Signal(object)
    monitoring_updated = Signal(object)
    streams_channels_dm_updated = Signal(object)
    streams_channels_ttm_updated = Signal(object)
    focus_sequence_updated = Signal(object)
