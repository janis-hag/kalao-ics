from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget

from compiled.ui_ttm_direct_control import Ui_TTMDirectControlWindow

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils.mixins import BackendActionMixin
from kalao.guis.utils.widgets import KMainWindow


class TTMDirectControlWindow(KMainWindow, BackendActionMixin):
    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend

        self.ui = Ui_TTMDirectControlWindow()
        self.ui.setupUi(self)

        self.resize(800, 125)

        self.show()
        self.center()
        self.setFixedSize(self.size())

    @Slot(int)
    def on_tip_slider_valueChanged(self, value: int) -> None:
        self.ui.tip_spinbox.setValue(value / 1000)

    @Slot(int)
    def on_tilt_slider_valueChanged(self, value: int) -> None:
        self.ui.tilt_spinbox.setValue(value / 1000)

    @Slot(float)
    def on_tip_spinbox_valueChanged(self, d: float) -> None:
        self.ui.tip_slider.setValue(round(d * 1000))

        self.action_send([], self.backend.ttm_position,
                         tip=self.ui.tip_spinbox.value(),
                         tilt=self.ui.tilt_spinbox.value())

    @Slot(float)
    def on_tilt_spinbox_valueChanged(self, d: float) -> None:
        self.ui.tilt_slider.setValue(round(d * 1000))

        self.action_send([], self.backend.ttm_position,
                         tip=self.ui.tip_spinbox.value(),
                         tilt=self.ui.tilt_spinbox.value())
