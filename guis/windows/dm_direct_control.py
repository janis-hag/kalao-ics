import numpy as np

from PySide6.QtCore import Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDoubleSpinBox, QLabel

from kalao.utils import kalao_tools, zernike

from guis.kalao.colormaps import CoolWarm
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOMainWindow


class DMSpinBox(QDoubleSpinBox):
    def __init__(self, colormap):
        super().__init__()

        self.colormap = colormap

        self.valueChanged.connect(self.change_color)

        self.setKeyboardTracking(False)
        self.setMinimum(-1.75)
        self.setMaximum(1.75)
        self.setSingleStep(0.05)

        self.setFixedSize(60, 60)
        self.setSuffix(' µm')

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
    zernike_indices = list(range(15))

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('dm_direct_control.ui', self)
        self.resize(400, 800)

        self.actuators_spinboxes = {}
        for i in range(140):
            x, y = kalao_tools.get_actuator_2d(i)
            spinbox = DMSpinBox(self.colormap)
            self.actuator_grid.addWidget(spinbox, x, y)

            spinbox.valueChanged.connect(
                lambda d, i=i: self.on_actuator_spinbox_valueChanged(d, i))

            self.actuators_spinboxes[i] = spinbox

        self.zernike_spinboxes = {}
        for i in self.zernike_indices:
            name, _ = zernike.get_coeff_name(i)

            label = QLabel(name)
            spinbox = QDoubleSpinBox()
            spinbox.setKeyboardTracking(False)
            spinbox.setMinimum(-1.75)
            spinbox.setMaximum(1.75)
            spinbox.setSingleStep(0.05)
            spinbox.setSuffix(' µm')
            self.zernike_groupbox.layout().addRow(label, spinbox)

            spinbox.valueChanged.connect(self.on_zernike_spinbox_valueChanged)

            self.zernike_spinboxes[i] = spinbox

        self.show()
        self.setFixedSize(self.size())

    def on_actuator_spinbox_valueChanged(self, d, i):
        if self.actuators_spinboxes[i].hasFocus():
            dm = np.zeros((12, 12))

            for k, s in self.actuators_spinboxes.items():
                i, j = kalao_tools.get_actuator_2d(k)

                dm[j, i] = s.value()

            self.backend.set_dm_to(dm)

    @Slot(bool)
    def on_reset_button_clicked(self, checked):
        self.all_slider.setValue(0)

    @Slot(int)
    def on_all_slider_valueChanged(self, value):
        for s in self.actuators_spinboxes.values():
            s.setValue(value / 100)

        dm = np.ones((12, 12)) * value / 100

        self.backend.set_dm_to(dm)

    def on_zernike_spinbox_valueChanged(self, d):
        self.compute_all()

    @Slot(float)
    def on_checkboard_amplitude_spinbox_valueChanged(self, d):
        self.compute_all()

    @Slot(float)
    def on_checkboard_period_spinbox_valueChanged(self, d):
        self.compute_all()

    @Slot(float)
    def on_grating_amplitude_spinbox_valueChanged(self, d):
        self.compute_all()

    @Slot(float)
    def on_grating_period_spinbox_valueChanged(self, d):
        self.compute_all()

    @Slot(float)
    def on_grating_angle_spinbox_valueChanged(self, d):
        self.compute_all()

    def compute_all(self):
        pattern = np.zeros((12, 12))

        pattern += self.compute_zernike()
        pattern += self.compute_checkboard()
        pattern += self.compute_grating()

        for i in range(140):
            x, y = kalao_tools.get_actuator_2d(i)
            self.actuators_spinboxes[i].setValue(pattern[x, y])

        self.backend.set_dm_to(pattern)

    def compute_zernike(self):
        coeffs = np.zeros(max(self.zernike_indices) + 1)

        for i in self.zernike_indices:
            coeffs[i] = self.zernike_spinboxes[i].value()

        return zernike.generate_pattern(coeffs, (12, 12))

    def compute_checkboard(self):
        amplitude = self.checkboard_amplitude_spinbox.value()
        period = self.checkboard_period_spinbox.value() // 2

        pattern = np.zeros((12, 12))
        for i in range(12):
            for j in range(12):
                pattern[i, j] = 2 * amplitude * (
                    (i//period + j//period) % 2 - 0.5)

        return pattern

    def compute_grating(self):
        amplitude = self.grating_amplitude_spinbox.value()
        period = 2 * np.pi / self.grating_period_spinbox.value()
        angle = self.grating_angle_spinbox.value() * np.pi / 180

        pattern = np.zeros((12, 12))
        for i in range(12):
            for j in range(12):
                k = kalao_tools.get_actuator_1d(i, j)

                if k is None:
                    continue

                pattern[i, j] = amplitude * np.cos(
                    period * (i * np.sin(angle) + j * np.cos(angle)))

        return pattern
