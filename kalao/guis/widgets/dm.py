from typing import Any

import numpy as np

from PySide6.QtCore import Signal
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget

from compiled.ui_dm import Ui_DMWidget

from kalao.common import zernike

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils import colormaps
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.widgets import KWidget

import config


class DMWidget(KWidget, BackendDataMixin):
    image_info = config.Images.dm01disp

    max_stroke = 1
    stroke_raw = np.nan
    stroke_effective = np.nan
    saturation = np.nan

    img = None
    masked = False

    hovered = Signal(str)

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend
        self.mask = zernike.generate_pattern_mask((12, 12))

        self.ui = Ui_DMWidget()
        self.ui.setupUi(self)

        self.resize(600, 400)

        self.ui.minmax_widget.setup(self.ui.dm_view, ' µm', 2, 1, -99, 99,
                                    self.image_info['min'],
                                    self.image_info['max'], symetric=True)
        self.ui.dm_view.set_data_md(' µm', 2)
        self.ui.dm_view.set_axis_md('', 0)

        self.change_units(Qt.CheckState.Unchecked)
        self.change_colormap(Qt.CheckState.Unchecked)

        self.ui.dm_view.hovered_str.connect(lambda string: self.hovered.emit(
            string))
        backend.streams_all_updated.connect(self.streams_all_updated)

    def streams_all_updated(self, data: dict[str, Any]) -> None:
        img = self.consume_shm(data, config.SHM.DM)

        max_stroke = self.consume_fps_param(data, config.FPS.BMC, 'max_stroke')

        if max_stroke is not None:
            self.max_stroke = max_stroke

        if img is not None:
            self.img = img
            self.update_view()

    def update_view(self) -> None:
        if self.img is None:
            return

        if self.masked:
            img = np.ma.masked_array(self.img, mask=self.mask,
                                     fill_value=np.nan)
        else:
            img = self.img

        img_min, img_max = self.ui.minmax_widget.compute_min_max(img)

        self.saturation = max(
            img.max() / self.image_info['max'],
            img.min() / self.image_info['min']) / self.max_stroke

        self.ui.dm_view.setImage(img, img_min, img_max)

        stroke_max = np.max(img)
        stroke_min = np.min(img)
        self.stroke_raw = stroke_max - stroke_min
        self.stroke_effective = min(stroke_max, 1.75 * self.max_stroke) - max(
            stroke_min, -1.75 * self.max_stroke)

        self.update_labels()

    def update_labels(self) -> None:
        self.ui.stroke_raw_label.updateText(
            stroke_raw=self.stroke_raw * self.ui.dm_view.data_scaling,
            unit=self.ui.dm_view.data_unit)
        self.ui.stroke_effective_label.updateText(
            stroke_effective=self.stroke_effective *
            self.ui.dm_view.data_scaling, unit=self.ui.dm_view.data_unit)

        if self.saturation >= 1:
            self.ui.saturation_label.setText('Saturated !')
            self.ui.saturation_label.setStyleSheet(
                f'color: {Color.RED.name()};')
        else:
            self.ui.saturation_label.updateText(saturation=self.saturation *
                                                100)
            self.ui.saturation_label.setStyleSheet('')

    def change_units(self, state: Qt.CheckState) -> None:
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.ui.minmax_widget.update_spinboxes_unit(' µm', 2, 2)
            self.ui.dm_view.set_data_md(' µm', 2, scaling=2)
        else:
            self.ui.minmax_widget.update_spinboxes_unit(' µm', 2, 1)
            self.ui.dm_view.set_data_md(' µm', 2, scaling=1)

        self.update_labels()

    def change_colormap(self, state: Qt.CheckState) -> None:
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.ui.dm_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.ui.dm_view.updateColormap(colormaps.CoolWarmTransparent())

    def change_mask(self, state: Qt.CheckState) -> None:
        self.masked = Qt.CheckState(state) == Qt.CheckState.Checked
        self.update_view()
