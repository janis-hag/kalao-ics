import time

from PySide2.QtCore import QObject, Signal


class AbstractBackend(QObject):
    updated = Signal()

    data = {}

    def update(self):
        start = time.monotonic()

        self.update_data()

        end = time.monotonic()

        self.data.update({'duration': end - start})

        self.updated.emit()

    def update_data(self):
        pass
