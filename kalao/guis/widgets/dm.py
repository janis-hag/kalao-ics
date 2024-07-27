import numpy as np

from PySide6.QtGui import Qt

from kalao.utils import zernike

from kalao.guis.utils import colormaps
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import (BackendDataMixin, MinMaxMixin,
                                     SceneHoverMixin)
from kalao.guis.utils.ui_loader import loadUi
from kalao.guis.utils.widgets import KWidget

import config


class DMWidget(KWidget, MinMaxMixin, SceneHoverMixin, BackendDataMixin):
    image_info = config.Images.dm01disp

    data_unit = ' µm'
    data_precision = 2

    axis_unit = ' px'
    axis_precision = 0

    max_stroke = 1
    stroke_raw = np.nan
    stroke_effective = np.nan
    saturation = np.nan

    img = None
    masked = False

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.mask = zernike.generate_pattern_mask((12, 12))

        loadUi('dm.ui', self)
        self.resize(600, 400)

        self.init_minmax(self.dm_view, symetric=True)

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        self.dm_view.hovered.connect(self.hover_xyv_to_str)
        backend.streams_all_updated.connect(self.streams_all_updated)

    def streams_all_updated(self, data):
        img = self.consume_shm(data, config.SHM.DM)

        max_stroke = self.consume_fps_param(data, config.FPS.BMC, 'max_stroke')

        if max_stroke is not None:
            self.max_stroke = max_stroke

        if img is not None:
            self.img = img
            self.update_view()

    def update_view(self):
        if self.img is None:
            return

        if self.masked:
            img = np.ma.masked_array(self.img, mask=self.mask,
                                     fill_value=np.nan)
        else:
            img = self.img

        img_min, img_max = self.compute_min_max(img)

        self.saturation = max(
            img.max() / self.image_info['max'],
            img.min() / self.image_info['min']) / self.max_stroke

        self.dm_view.setImage(img, img_min, img_max)

        stroke_max = np.max(img)
        stroke_min = np.min(img)
        self.stroke_raw = stroke_max - stroke_min
        self.stroke_effective = min(stroke_max, 1.75 * self.max_stroke) - max(
            stroke_min, -1.75 * self.max_stroke)

        self.update_labels()

    def update_labels(self):
        self.stroke_raw_label.updateText(
            stroke_raw=self.stroke_raw * self.data_scaling,
            unit=self.data_unit)
        self.stroke_effective_label.updateText(
            stroke_effective=self.stroke_effective * self.data_scaling,
            unit=self.data_unit)

        if self.saturation >= 1:
            self.saturation_label.setText('Saturated !')
            self.saturation_label.setStyleSheet(f'color: {Color.RED.name()};')
        else:
            self.saturation_label.updateText(saturation=self.saturation * 100)
            self.saturation_label.setStyleSheet('')

    def change_units(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.update_spinboxes_unit(' µm', 2, 2)
        else:
            self.update_spinboxes_unit(' µm', 1, 2)

        self.update_labels()

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.dm_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.dm_view.updateColormap(colormaps.CoolWarmTransparent())

    def change_mask(self, state):
        self.masked = Qt.CheckState(state) == Qt.Checked
        self.update_view()
