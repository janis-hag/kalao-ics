import numpy as np

from PySide2.QtGui import Qt

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

    #TODO: modify stream_info with stroke_max?

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('dm.ui', self)
        self.resize(600, 400)

        MinMaxMixin.__init__(self)

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        self.dm_view.hovered.connect(self.hover_event)
        backend.updated.connect(self.data_updated)

    def data_updated(self):
        img = self.backend.data['dm01disp']['stream'] * self.data_scaling
        max_stroke = self.backend.data['dm01disp'][
            'max_stroke'] * self.data_scaling

        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            abs_max = max(abs(img_min), abs(img_max))
            img_min = -abs_max
            img_max = abs_max

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.dm_view.setImage(img, img_min, img_max)

        stroke_max = np.max(img)
        stroke_min = np.min(img)
        stroke_raw = stroke_max - stroke_min
        stroke_effective = min(stroke_max, 1.75 * max_stroke) - max(
            stroke_min, -1.75 * max_stroke)

        self.stroke_raw_label.updateText(stroke_raw=stroke_raw,
                                         unit=self.data_unit)
        self.stroke_effective_label.updateText(
            stroke_effective=stroke_effective, unit=self.data_unit)

    def change_units(self, state):
        if state == Qt.Checked:
            self.data_unit = ' um'
            self.data_scaling = 2
        else:
            self.data_unit = ' um'
            self.data_scaling = 1

        self.update_spinboxes_unit()

    def change_colormap(self, state):
        if state == Qt.Checked:
            self.dm_view.setColormap(colormaps.GrayscaleSaturation())
        else:
            self.dm_view.setColormap(colormaps.CoolWarm())
