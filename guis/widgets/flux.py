import numpy as np

from PySide6.QtGui import Qt

from kalao.utils import ktools

from guis.kalao import colormaps
from guis.kalao.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KWidget

import config


class FluxWidget(KWidget, MinMaxMixin, SceneHoverMixin, BackendDataMixin):
    associated_stream = config.Streams.FLUX
    stream_info = config.StreamInfo.shwfs_slopes_flux

    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0

    flux_avg = np.nan
    flux_brightest = np.nan

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.mask = ktools.generate_flux_mask_from_subaps(
            config.WFS.masked_subaps)

        loadUi('flux.ui', self)
        self.resize(600, 400)

        self.init_minmax(self.flux_view)

        self.update_labels()
        self.change_colormap(Qt.Unchecked)

        self.flux_view.hovered.connect(self.hover_xyv_to_str)
        backend.streams_updated.connect(self.streams_updated)

    def streams_updated(self, data):
        img = self.consume_stream(data, config.Streams.FLUX)

        if img is not None:
            img = np.ma.masked_array(img, mask=self.mask, fill_value=np.nan)

            img_min, img_max = self.compute_min_max(img)

            if img.max() >= self.stream_info['max']:
                self.saturation_label.setText('Saturated !')
            else:
                self.saturation_label.setText('')

            self.flux_view.setImage(img, img_min, img_max)

        flux_avg = self.consume_param(data, config.FPS.SHWFS,
                                      'flux_subaperture_avg')
        if flux_avg is not None:
            self.flux_avg = flux_avg

        flux_brightest = self.consume_param(data, config.FPS.SHWFS,
                                            'flux_subaperture_brightest')
        if flux_brightest is not None:
            self.flux_brightest = flux_brightest

        if flux_avg is not None or flux_brightest is not None:
            self.update_labels()

    def update_labels(self):
        self.flux_avg_label.updateText(
            flux_avg=self.flux_avg * self.data_scaling, unit=self.data_unit)
        self.flux_brightest_label.updateText(
            flux_brightest=self.flux_brightest * self.data_scaling,
            unit=self.data_unit)

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.flux_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.flux_view.updateColormap(colormaps.BlackBodyTransparent())
