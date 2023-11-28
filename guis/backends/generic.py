from PySide2.QtCore import QObject, Signal


class GenericBackend(QObject):
    updated = Signal()

    data = {}

    def update(self):
        self.updated.emit()