import numpy as np

from PySide6.QtCore import Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDoubleSpinBox

from kalao.utils import kalao_tools

from guis.kalao.colormaps import CoolWarm
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOMainWindow


class DMSpinBox(QDoubleSpinBox):
    def __init__(self, colormap):
        super().__init__()

        self.colormap = colormap

        self.valueChanged.connect(self.change_color)

        self.setMinimum(-1.75)
        self.setMaximum(1.75)
        self.setSingleStep(0.05)
        self.setFixedSize(60, 60)
        self.setSuffix(' um')

        self.change_color(self.value())

    def heightForWidth(self, w):
        return w

    def change_color(self, d):
        d = 255 * (d - self.minimum()) / (self.maximum() - self.minimum())

        color = self.colormap.colormap[round(d)]
        color = QColor(color).name()

        self.setStyleSheet(f"background-color: {color};")


class DMDirectControl(KalAOMainWindow):
    colormap = CoolWarm()

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('dm_direct_control.ui', self)
        self.resize(400, 800)

        self.spinboxes = {}

        for i in range(140):
            x, y = kalao_tools.get_actuator_2d(i)
            spinbox = DMSpinBox(self.colormap)
            self.actuator_grid.addWidget(spinbox, x, y)

            spinbox.valueChanged.connect(lambda d, i=i: self.
                                         on_spinbox_valueChanged(d, i))

            self.spinboxes[i] = spinbox

        self.show()
        self.setFixedSize(self.size())

    def on_spinbox_valueChanged(self, d, i):
        if self.spinboxes[i].hasFocus():
            dm = np.zeros((12, 12))

            for k, s in self.spinboxes.items():
                i, j = kalao_tools.get_actuator_2d(k)

                dm[j, i] = s.value()

            self.backend.set_dm_to(dm)

    @Slot(bool)
    def on_reset_button_clicked(self, checked):
        self.all_slider.setValue(0)

    @Slot(int)
    def on_all_slider_valueChanged(self, value):
        for s in self.spinboxes.values():
            s.setValue(value / 100)

        dm = np.ones((12, 12)) * value / 100

        self.backend.set_dm_to(dm)
