from PySide6.QtGui import Qt

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

        MinMaxMixin.init(self)

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        self.slopes_view.hovered.connect(self.hover_event)
        backend.streams_updated.connect(self.data_updated)

    def data_updated(self):
        img = self.backend.consume_stream(self.backend.streams,
                                          config.Streams.SLOPES)

        if img is not None:
            img_min, img_max = self.compute_min_max(img, symetric=True)

            self.slopes_view.setImage(img, img_min, img_max)

        slope_x = self.backend.consume_param(self.backend.streams,
                                             'shwfs_process-1', 'slope_x')
        if slope_x is not None:
            self.tip_label.updateText(tip=slope_x * self.data_scaling,
                                      unit=self.data_unit)

        slope_y = self.backend.consume_param(self.backend.streams,
                                             'shwfs_process-1', 'slope_y')
        if slope_y is not None:
            self.tilt_label.updateText(tilt=slope_y * self.data_scaling,
                                       unit=self.data_unit)

        residual = self.backend.consume_param(self.backend.streams,
                                              'shwfs_process-1', 'residual')
        if residual is not None:
            self.residual_label.updateText(
                residual=residual * self.data_scaling, unit=self.data_unit)

    def change_units(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.data_unit = ' asec'
            self.data_scaling = config.WFS.plate_scale
        else:
            self.data_unit = ' px'
            self.data_scaling = 1

        self.update_spinboxes_unit()

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.slopes_view.setColormap(colormaps.GrayscaleSaturation())
        else:
            self.slopes_view.setColormap(colormaps.CoolWarm())
