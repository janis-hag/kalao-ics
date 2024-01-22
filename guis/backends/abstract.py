import time
from datetime import datetime, timezone
from functools import wraps

from PySide6.QtCore import QObject, Signal


def timeit(fun):
    @wraps(fun)
    def wrapper(self, *args, **kwargs):
        start = time.monotonic()

        data = fun(self, *args, **kwargs)

        end = time.monotonic()

        data.update({
            'metadata': {
                'duration': end - start,
                'timestamp': datetime.now(timezone.utc)
            }
        })

        return data

    return wrapper


def name_to_url(name):
    return '/' + name.removeprefix('set_').removeprefix('get_').replace(
        '_', '/')


class AbstractBackend(QObject):
    streams_all_updated = Signal(object)
    streams_fli_updated = Signal(object)
    all_updated = Signal(object)
    monitoringandtelemetry_updated = Signal(object)
    streams_dmdisp_updated = Signal(object)
    focus_updated = Signal(object)

    _emit = True
