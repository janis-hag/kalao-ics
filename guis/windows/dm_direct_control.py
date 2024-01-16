from pathlib import Path

import numpy as np

from astropy.io import fits

from PySide6.QtCore import QSignalBlocker, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QDoubleSpinBox, QErrorMessage, QFileDialog,
                               QLabel)

from kalao.utils import ktools, zernike

from guis.kalao.colormaps import CoolWarm
from guis.kalao.mixins import BackendActionMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KMainWindow


class DMSpinBox(QDoubleSpinBox):
    def __init__(self, colormap):
        super().__init__()

        self.colormap = colormap

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
        d = np.clip(d, 0, 255)

        color = self.colormap.colormap[round(d)]
        color = QColor(color).name()

        self.setStyleSheet(f"background-color: {color};")

    def setValue(self, val):
        self.change_color(val)
        super().setValue(val)


class DMDirectControlWindow(KMainWindow, BackendActionMixin):
    colormap = CoolWarm()
    zernike_indices = list(range(15))

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('dm_direct_control.ui', self)
        self.resize(400, 800)

        self.actuators_spinboxes = {}
        for i in range(140):
            x, y = ktools.get_actuator_2d(i)
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

        self.error_dialog = QErrorMessage(self)

        self.show()
        self.center()
        self.setFixedSize(self.size())

    def on_actuator_spinbox_valueChanged(self, d, i):
        self.actuators_spinboxes[i].change_color(d)

        pattern = np.zeros((12, 12))

        for i, spinbox in self.actuators_spinboxes.items():
            j, k = ktools.get_actuator_2d(i)
            pattern[j, k] = spinbox.value()

        self.action_send([], self.backend.set_dm_pattern, pattern)

    @Slot(bool)
    def on_reset_button_clicked(self, checked):
        with QSignalBlocker(self.all_slider):
            self.all_slider.setValue(0)

        for s in self.actuators_spinboxes.values():
            with QSignalBlocker(s):
                s.setValue(0)

        self.reset_all_sides_boxes()

        self.action_send([], self.backend.set_dm_pattern, np.zeros((12, 12)))

    @Slot(bool)
    def on_load_button_clicked(self, checked):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter(
            'All (*.fits *.csv);;Images (*.fits);;Text files (*.csv)')
        dialog.setAcceptMode(QFileDialog.AcceptOpen)

        try:
            if dialog.exec():
                filenames = dialog.selectedFiles()

                if len(filenames) != 1:
                    self.error_dialog.showMessage(
                        f'Select only one file (got {len(filenames)}).')
                    return

                filename = Path(filenames[0])

                if not filename.exists():
                    self.error_dialog.showMessage('File does not exists.')
                    return

                if filename.suffix.lower() == '.fits':
                    img = fits.getdata(filename)

                    if img.shape != (12, 12):
                        self.error_dialog.showMessage(
                            f'FITS shape incorrect (expected {(12, 12)}, got {img.shape}).'
                        )
                        return

                    self.set_spinboxes_to_pattern(img)
                    self.action_send([], self.backend.set_dm_pattern, img)

                elif filename.suffix.lower() == '.csv':
                    data = np.loadtxt(filename)

                    if data.shape != (140, ):
                        self.error_dialog.showMessage(
                            f'CSV shape incorrect (expected {(140,)}, got {data.shape}).'
                        )
                        return

                    pattern = np.zeros((12, 12))
                    for i in range(140):
                        j, k = ktools.get_actuator_2d(i)
                        pattern[j, k] = data[i]

                    self.set_spinboxes_to_pattern(pattern)
                    self.action_send([], self.backend.set_dm_pattern, pattern)

                else:
                    self.error_dialog.showMessage(
                        f'Unsupported file extension "{filename.suffix}".')
        except PermissionError:
            self.error_dialog.showMessage(
                'Can\'t read file, permission refused.')

    @Slot(bool)
    def on_save_button_clicked(self, checked):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setNameFilter(
            'All (*.fits *.csv);;Images (*.fits);;Text files (*.csv)')
        dialog.setAcceptMode(QFileDialog.AcceptSave)

        try:
            if dialog.exec():
                filenames = dialog.selectedFiles()

                if len(filenames) != 1:
                    self.error_dialog.showMessage(
                        f'Select only one file (got {len(filenames)}).')
                    return

                filename = Path(filenames[0])

                if filename.suffix.lower() == '.fits':
                    pattern = np.zeros((12, 12))

                    for i, spinbox in self.actuators_spinboxes.items():
                        j, k = ktools.get_actuator_2d(i)
                        pattern[j, k] = spinbox.value()

                    fits.PrimaryHDU(pattern).writeto(filename, overwrite=True)

                elif filename.suffix.lower() == '.csv':
                    pattern = np.zeros((140, ))

                    for i, spinbox in self.actuators_spinboxes.items():
                        pattern[i] = spinbox.value()

                    np.savetxt(filename, pattern)

                else:
                    self.error_dialog.showMessage(
                        f'Unsupported file extension "{filename.suffix}".')
        except PermissionError:
            self.error_dialog.showMessage(
                'Can\'t write file, permission refused.')

    def set_spinboxes_to_pattern(self, pattern):
        for i, spinbox in self.actuators_spinboxes.items():
            x, y = ktools.get_actuator_2d(i)

            with QSignalBlocker(spinbox):
                spinbox.setValue(pattern[x, y])

    @Slot(int)
    def on_all_slider_valueChanged(self, value):
        self.reset_all_sides_boxes()

        pattern = np.ones((12, 12)) * value / 100

        self.set_spinboxes_to_pattern(pattern)
        self.action_send([], self.backend.set_dm_pattern, pattern)

    def on_zernike_spinbox_valueChanged(self, d):
        self.compute_all()

    @Slot(float)
    def on_checkerboard_amplitude_spinbox_valueChanged(self, d):
        self.compute_all()

    @Slot(float)
    def on_checkerboard_period_spinbox_valueChanged(self, d):
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

    def reset_all_sides_boxes(self):
        for s in self.zernike_spinboxes.values():
            with QSignalBlocker(s):
                s.setValue(0)

        with QSignalBlocker(self.checkerboard_amplitude_spinbox):
            self.checkerboard_amplitude_spinbox.setValue(0)

        with QSignalBlocker(self.checkerboard_period_spinbox):
            self.checkerboard_period_spinbox.setValue(2)

        with QSignalBlocker(self.grating_amplitude_spinbox):
            self.grating_amplitude_spinbox.setValue(0)

        with QSignalBlocker(self.grating_period_spinbox):
            self.grating_period_spinbox.setValue(2)

        with QSignalBlocker(self.grating_angle_spinbox):
            self.grating_angle_spinbox.setValue(0)

    def compute_all(self):
        pattern = np.zeros((12, 12))

        pattern += self.compute_zernike()
        pattern += self.compute_checkerboard()
        pattern += self.compute_grating()

        self.set_spinboxes_to_pattern(pattern)
        self.action_send([], self.backend.set_dm_pattern, pattern)

    def compute_zernike(self):
        coeffs = np.zeros(max(self.zernike_indices) + 1)

        for i in self.zernike_indices:
            coeffs[i] = self.zernike_spinboxes[i].value()

        return zernike.generate_pattern(coeffs, (12, 12))

    def compute_checkerboard(self):
        amplitude = self.checkerboard_amplitude_spinbox.value()
        period = self.checkerboard_period_spinbox.value() // 2

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
                k = ktools.get_actuator_1d(i, j)

                if k is None:
                    continue

                pattern[i, j] = amplitude * np.cos(
                    period * (i * np.sin(angle) + j * np.cos(angle)))

        return pattern
