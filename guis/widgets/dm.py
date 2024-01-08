import numpy as np

from PySide6.QtGui import Qt

from guis.kalao import colormaps
from guis.kalao.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KWidget

import config


class DMWidget(KWidget, MinMaxMixin, SceneHoverMixin, BackendDataMixin):
    associated_stream = config.Streams.DM
    stream_info = config.StreamInfo.dm01disp

    data_unit = ' µm'
    data_precision = 2

    axis_unit = ' px'
    axis_precision = 0

    max_stroke = 1
    stroke_raw = np.nan
    stroke_effective = np.nan

    #TODO: modify stream_info with stroke_max?

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('dm.ui', self)
        self.resize(600, 400)

        self.init_minmax(self.dm_view, symetric=True)

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        self.dm_view.hovered.connect(self.hover_xyv_to_str)
        backend.streams_updated.connect(self.streams_updated)

    def streams_updated(self, data):
        img = self.consume_stream(data, config.Streams.DM)

        max_stroke = self.consume_param(data, config.FPS.BMC, 'max_stroke')

        if max_stroke is not None:
            self.max_stroke = max_stroke

        if img is not None:
            img_min, img_max = self.compute_min_max(img)

            if img.min(
            ) <= self.stream_info['min'] * self.max_stroke or img.max(
            ) >= self.stream_info['max'] * self.max_stroke:
                self.saturation_label.setText('Saturated !')
            else:
                self.saturation_label.setText('')

            self.dm_view.setImage(img, img_min, img_max)

            stroke_max = np.max(img)
            stroke_min = np.min(img)
            self.stroke_raw = stroke_max - stroke_min
            self.stroke_effective = min(
                stroke_max, 1.75 * self.max_stroke) - max(
                    stroke_min, -1.75 * self.max_stroke)

            self.update_labels()

    def update_labels(self):
        self.stroke_raw_label.updateText(
            stroke_raw=self.stroke_raw * self.data_scaling,
            unit=self.data_unit)
        self.stroke_effective_label.updateText(
            stroke_effective=self.stroke_effective * self.data_scaling,
            unit=self.data_unit)

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
            self.dm_view.updateColormap(colormaps.CoolWarm())
