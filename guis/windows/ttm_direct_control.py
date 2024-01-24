import numpy as np

from PySide6.QtCore import Slot

from guis.utils.mixins import BackendActionMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KMainWindow


class TTMDirectControlWindow(KMainWindow, BackendActionMixin):
    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('ttm_direct_control.ui', self)
        self.resize(800, 125)

        self.show()
        self.center()
        self.setFixedSize(self.size())

    @Slot(int)
    def on_tip_slider_valueChanged(self, value):
        self.tip_spinbox.setValue(value / 1000)

    @Slot(int)
    def on_tilt_slider_valueChanged(self, value):
        self.tilt_spinbox.setValue(value / 1000)

    @Slot(float)
    def on_tip_spinbox_valueChanged(self, d):
        self.tip_slider.setValue(round(d * 1000))

        tiptilt = np.array([
            self.tip_spinbox.value(),
            self.tilt_spinbox.value()
        ])

        self.action_send([], self.backend.set_ttm_pattern, tiptilt)

    @Slot(float)
    def on_tilt_spinbox_valueChanged(self, d):
        self.tilt_slider.setValue(round(d * 1000))

        tiptilt = np.array([
            self.tip_spinbox.value(),
            self.tilt_spinbox.value()
        ])

        self.action_send([], self.backend.set_ttm_pattern, tiptilt)
