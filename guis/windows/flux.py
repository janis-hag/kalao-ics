from PySide6.QtGui import Qt

from guis.kalao import colormaps
from guis.kalao.mixins import HoverMixin, MinMaxMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

import config


class FluxWidget(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = config.Streams.FLUX
    stream_info = config.StreamInfo.shwfs_slopes_flux
    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('flux.ui', self)
        self.resize(600, 400)

        MinMaxMixin.init(self)

        self.change_colormap(Qt.Unchecked)

        self.flux_view.hovered.connect(self.hover_event)
        backend.streams_updated.connect(self.data_updated)

    def data_updated(self):
        img = self.backend.consume_stream(self.backend.streams,
                                          config.Streams.FLUX)

        if img is not None:
            img_min, img_max = self.compute_min_max(img)

            self.flux_view.setImage(img, img_min, img_max)

        flux_avg = self.backend.consume_param(self.backend.streams,
                                              config.FPS.SHWFS,
                                              'flux_subaperture_avg')
        if flux_avg is not None:
            self.flux_avg_label.updateText(
                flux_avg=flux_avg * self.data_scaling, unit=self.data_unit)

        flux_brightest = self.backend.consume_param(
            self.backend.streams, config.FPS.SHWFS,
            'flux_subaperture_brightest')
        if flux_brightest is not None:
            self.flux_brightest_label.updateText(
                flux_brightest=flux_brightest * self.data_scaling,
                unit=self.data_unit)

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.flux_view.setColormap(colormaps.GrayscaleSaturation())
        else:
            self.flux_view.setColormap(colormaps.BlackBody())
