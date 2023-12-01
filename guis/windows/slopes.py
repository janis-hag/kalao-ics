from PySide2.QtGui import Qt

from guis.kalao import colormaps
from guis.kalao.mixins import HoverMixin, MinMaxMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

import config


class SlopesWidget(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = config.Streams.SLOPES
    stream_info = config.StreamInfo.shwfs_slopes
    data_unit = ' px'
    data_precision = 3

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('slopes.ui', self)
        self.resize(600, 400)

        MinMaxMixin.__init__(self)

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        self.slopes_view.hovered.connect(self.hover_event)
        backend.updated.connect(self.data_updated)

    def data_updated(self):
        img = self.backend.data['shwfs_slopes']['stream'] * self.data_scaling
        tip = self.backend.data['shwfs_slopes']['tip'] * self.data_scaling
        tilt = self.backend.data['shwfs_slopes']['tilt'] * self.data_scaling
        residual = self.backend.data['shwfs_slopes'][
            'residual'] * self.data_scaling

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

        self.slopes_view.setImage(img, img_min, img_max)

        self.tip_label.updateText(tip=tip, unit=self.data_unit)
        self.tilt_label.updateText(tilt=tilt, unit=self.data_unit)
        self.residual_label.updateText(residual=residual, unit=self.data_unit)

    def change_units(self, state):
        if state == Qt.Checked:
            self.data_unit = ' asec'
            self.data_scaling = config.WFS.plate_scale
        else:
            self.data_unit = ' px'
            self.data_scaling = 1

        self.update_spinboxes_unit()

    def change_colormap(self, state):
        if state == Qt.Checked:
            self.slopes_view.setColormap(colormaps.GrayscaleSaturation())
        else:
            self.slopes_view.setColormap(colormaps.CoolWarm())
