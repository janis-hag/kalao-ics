import numpy as np

from PySide6.QtGui import Qt

from guis.kalao import colormaps
from guis.kalao.mixins import HoverMixin, MinMaxMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

import config


class DMWidget(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = config.Streams.DM
    stream_info = config.StreamInfo.dm01disp
    data_unit = ' um'
    data_precision = 3

    axis_unit = ' px'
    axis_precision = 0

    max_stroke = 1

    #TODO: modify stream_info with stroke_max?

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('dm.ui', self)
        self.resize(600, 400)

        MinMaxMixin.init(self)

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        self.dm_view.hovered.connect(self.hover_event)
        backend.streams_updated.connect(self.data_updated)

    def data_updated(self):
        img = self.backend.consume_stream(self.backend.streams,
                                          config.Streams.DM)

        max_stroke = self.backend.consume_param(self.backend.streams,
                                                'bmc_display-1', 'max_stroke')

        if max_stroke is not None:
            self.max_stroke = max_stroke

        if img is not None:
            img_min, img_max = self.compute_min_max(img, symetric=True)

            self.dm_view.setImage(img, img_min, img_max)

            stroke_max = np.max(img)
            stroke_min = np.min(img)
            stroke_raw = stroke_max - stroke_min
            stroke_effective = min(stroke_max, 1.75 * self.max_stroke) - max(
                stroke_min, -1.75 * self.max_stroke)

            self.stroke_raw_label.updateText(
                stroke_raw=stroke_raw * self.data_scaling, unit=self.data_unit)
            self.stroke_effective_label.updateText(
                stroke_effective=stroke_effective * self.data_scaling,
                unit=self.data_unit)

    def change_units(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.data_unit = ' um'
            self.data_scaling = 2
        else:
            self.data_unit = ' um'
            self.data_scaling = 1

        self.update_spinboxes_unit()

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.dm_view.setColormap(colormaps.GrayscaleSaturation())
        else:
            self.dm_view.setColormap(colormaps.CoolWarm())
