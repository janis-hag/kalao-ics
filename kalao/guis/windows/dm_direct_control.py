from pathlib import Path

import numpy as np

from astropy.io import fits

from PySide6.QtCore import QSignalBlocker, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QDoubleSpinBox, QFileDialog, QLabel,
                               QMessageBox, QWidget)

from compiled.ui_dm_direct_control import Ui_DMDirectControlWindow

from kalao.utils import ktools, zernike

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils.colormaps import Colormap, CoolWarm
from kalao.guis.utils.mixins import BackendActionMixin
from kalao.guis.utils.widgets import KMainWindow, KMessageBox

import config


class DMSpinBox(QDoubleSpinBox):
    def __init__(self, colormap: Colormap) -> None:
        super().__init__()

        self.colormap = colormap

        self.setKeyboardTracking(False)
        self.setMinimum(-1.75)
        self.setMaximum(1.75)
        self.setSingleStep(0.05)

        self.setFixedSize(60, 60)
        self.setSuffix(' µm')

        self.change_color(self.value())

    def heightForWidth(self, w: int) -> int:
        return w

    def change_color(self, d: float) -> None:
        d = 255 * (d - self.minimum()) / (self.maximum() - self.minimum())
        d = np.clip(d, 0, 255)

        color = self.colormap.table[round(d)]
        color = QColor(color).name()

        self.setStyleSheet(f'background-color: {color};')

    def setValue(self, val: float) -> None:
        self.change_color(val)
        super().setValue(val)


class DMDirectControlWindow(KMainWindow, BackendActionMixin):
    colormap = CoolWarm()
    zernike_indices = list(range(15))

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend

        self.ui = Ui_DMDirectControlWindow()
        self.ui.setupUi(self)

        self.resize(400, 800)

        self.actuators_spinboxes = {}
        for i in range(140):
            x, y = ktools.get_actuator_2d(i)
            spinbox = DMSpinBox(self.colormap)
            self.ui.actuator_grid.addWidget(spinbox, x, y)

            spinbox.valueChanged.connect(
                lambda d, _i=i: self.on_actuator_spinbox_valueChanged(d, _i))

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
            self.ui.zernike_groupbox.layout().addRow(label, spinbox)

            spinbox.valueChanged.connect(self.on_zernike_spinbox_valueChanged)

            self.zernike_spinboxes[i] = spinbox

        self.error_dialog = KMessageBox(self)
        self.error_dialog.setIcon(QMessageBox.Icon.Critical)
        self.error_dialog.setModal(True)

        self.show()
        self.center()
        self.setFixedSize(self.size())

    def on_actuator_spinbox_valueChanged(self, d: float, i: int) -> None:
        self.actuators_spinboxes[i].change_color(d)

        pattern = np.zeros(config.DM.shape)

        for i, spinbox in self.actuators_spinboxes.items():
            j, k = ktools.get_actuator_2d(i)
            pattern[j, k] = spinbox.value()

        self.action_send([], self.backend.dm_pattern, pattern=pattern)

    @Slot(bool)
    def on_reset_button_clicked(self, checked: bool) -> None:
        with QSignalBlocker(self.ui.all_slider):
            self.ui.all_slider.setValue(0)

        for s in self.actuators_spinboxes.values():
            with QSignalBlocker(s):
                s.setValue(0)

        self.reset_all_sides_boxes()

        self.action_send([], self.backend.dm_pattern,
                         pattern=np.zeros(config.DM.shape))

    @Slot(bool)
    def on_load_button_clicked(self, checked: bool) -> None:
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilter(
            'All (*.fits *.csv);;Images (*.fits);;Text files (*.csv)')
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)

        self.error_dialog.setText('<b>Loading failed!</b>')

        try:
            if dialog.exec():
                filenames = dialog.selectedFiles()

                if len(filenames) != 1:
                    self.error_dialog.setInformativeText(
                        f'Select one and only one file (got {len(filenames)}).'
                    )
                    self.error_dialog.show()
                    return

                filename = Path(filenames[0])

                if not filename.exists():
                    self.error_dialog.setInformativeText(
                        'File does not exists.')
                    self.error_dialog.show()
                    return

                if filename.suffix.lower() == '.fits':
                    img = fits.getdata(filename)

                    if img.shape != config.DM.shape:
                        self.error_dialog.setInformativeText(
                            f'FITS shape incorrect (expected {config.DM.shape}, got {img.shape}).'
                        )
                        self.error_dialog.show()
                        return

                    self.set_spinboxes_to_pattern(img)
                    self.action_send([], self.backend.dm_pattern, pattern=img)

                elif filename.suffix.lower() == '.csv':
                    data = np.loadtxt(filename)

                    if data.shape != (140, ):
                        self.error_dialog.setInformativeText(
                            f'CSV shape incorrect (expected {(140,)}, got {data.shape}).'
                        )
                        self.error_dialog.show()
                        return

                    pattern = np.zeros(config.DM.shape)
                    for i in range(140):
                        j, k = ktools.get_actuator_2d(i)
                        pattern[j, k] = data[i]

                    self.set_spinboxes_to_pattern(pattern)
                    self.action_send([], self.backend.dm_pattern,
                                     pattern=pattern)

                else:
                    self.error_dialog.setInformativeText(
                        f'Unsupported file extension "{filename.suffix}".')
                    self.error_dialog.show()
        except PermissionError:
            self.error_dialog.setInformativeText(
                'Can\'t read file, permission refused.')
            self.error_dialog.show()

    @Slot(bool)
    def on_save_button_clicked(self, checked: bool) -> None:
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setNameFilter(
            'All (*.fits *.csv);;Images (*.fits);;Text files (*.csv)')
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

        self.error_dialog.setText('<b>Saving failed!</b>')

        try:
            if dialog.exec():
                filenames = dialog.selectedFiles()

                if len(filenames) != 1:
                    self.error_dialog.setInformativeText(
                        f'Select one and only one file (got {len(filenames)}).'
                    )
                    self.error_dialog.show()
                    return

                filename = Path(filenames[0])

                if filename.suffix.lower() == '.fits':
                    pattern = np.zeros(config.DM.shape)

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
                    self.error_dialog.setInformativeText(
                        f'Unsupported file extension "{filename.suffix}".')
                    self.error_dialog.show()
        except PermissionError:
            self.error_dialog.setInformativeText(
                'Can\'t write file, permission refused.')
            self.error_dialog.show()

    def set_spinboxes_to_pattern(self, pattern: np.ndarray[float]) -> None:
        for i, spinbox in self.actuators_spinboxes.items():
            x, y = ktools.get_actuator_2d(i)

            with QSignalBlocker(spinbox):
                spinbox.setValue(pattern[x, y])

    @Slot(int)
    def on_all_slider_valueChanged(self, value: int) -> None:
        self.reset_all_sides_boxes()

        pattern = np.full(config.DM.shape, value / 100)

        self.set_spinboxes_to_pattern(pattern)
        self.action_send([], self.backend.dm_pattern, pattern=pattern)

    def on_zernike_spinbox_valueChanged(self, d: float) -> None:
        self.compute_all()

    @Slot(float)
    def on_checkerboard_amplitude_spinbox_valueChanged(self, d: float) -> None:
        self.compute_all()

    @Slot(float)
    def on_checkerboard_period_spinbox_valueChanged(self, d: float) -> None:
        self.compute_all()

    @Slot(float)
    def on_grating_amplitude_spinbox_valueChanged(self, d: float) -> None:
        self.compute_all()

    @Slot(float)
    def on_grating_period_spinbox_valueChanged(self, d: float) -> None:
        self.compute_all()

    @Slot(float)
    def on_grating_angle_spinbox_valueChanged(self, d: float) -> None:
        self.compute_all()

    def reset_all_sides_boxes(self) -> None:
        for s in self.zernike_spinboxes.values():
            with QSignalBlocker(s):
                s.setValue(0)

        with QSignalBlocker(self.ui.checkerboard_amplitude_spinbox):
            self.ui.checkerboard_amplitude_spinbox.setValue(0)

        with QSignalBlocker(self.ui.checkerboard_period_spinbox):
            self.ui.checkerboard_period_spinbox.setValue(2)

        with QSignalBlocker(self.ui.grating_amplitude_spinbox):
            self.ui.grating_amplitude_spinbox.setValue(0)

        with QSignalBlocker(self.ui.grating_period_spinbox):
            self.ui.grating_period_spinbox.setValue(2)

        with QSignalBlocker(self.ui.grating_angle_spinbox):
            self.ui.grating_angle_spinbox.setValue(0)

    def compute_all(self) -> None:
        pattern = np.zeros(config.DM.shape, dtype=float)

        pattern += self.compute_zernike()
        pattern += self.compute_checkerboard()
        pattern += self.compute_grating()

        self.set_spinboxes_to_pattern(pattern)
        self.action_send([], self.backend.dm_pattern, pattern=pattern)

    def compute_zernike(self) -> np.ndarray:
        coeffs = np.zeros(max(self.zernike_indices) + 1)

        for i in self.zernike_indices:
            coeffs[i] = self.zernike_spinboxes[i].value()

        return zernike.generate_pattern(coeffs, config.DM.shape)

    def compute_checkerboard(self) -> np.ndarray:
        amplitude = self.ui.checkerboard_amplitude_spinbox.value()
        period = self.ui.checkerboard_period_spinbox.value() // 2

        pattern = np.zeros(config.DM.shape)
        for i in range(12):
            for j in range(12):
                pattern[i, j] = 2 * amplitude * (
                    (i//period + j//period) % 2 - 0.5)

        return pattern

    def compute_grating(self) -> np.ndarray:
        amplitude = self.ui.grating_amplitude_spinbox.value()
        period = 2 * np.pi / self.ui.grating_period_spinbox.value()
        angle = self.ui.grating_angle_spinbox.value() * np.pi / 180

        pattern = np.zeros(config.DM.shape)
        for i in range(12):
            for j in range(12):
                k = ktools.get_actuator_1d(i, j)

                if k is None:
                    continue

                pattern[i, j] = amplitude * np.cos(
                    period * (i * np.sin(angle) + j * np.cos(angle)))

        return pattern
