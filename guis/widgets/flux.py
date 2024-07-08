import numpy as np

from PySide6.QtGui import Qt

from kalao.utils import ktools

from guis.utils import colormaps
from guis.utils.definitions import Color
from guis.utils.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KWidget

import config


class FluxWidget(KWidget, MinMaxMixin, SceneHoverMixin, BackendDataMixin):
    image_info = config.Images.shwfs_flux

    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0

    saturation = np.nan
    flux_avg = np.nan
    flux_brightest = np.nan

    img = None
    masked = False

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
        backend.streams_all_updated.connect(self.streams_all_updated)

    def streams_all_updated(self, data):
        img = self.consume_shm(data, config.SHM.FLUX)

        if img is not None:
            self.img = img
            self.update_view()

        flux_avg = self.consume_fps_param(data, config.FPS.SHWFS, 'flux_avg')
        if flux_avg is not None:
            self.flux_avg = flux_avg

        flux_brightest = self.consume_fps_param(data, config.FPS.SHWFS,
                                                'flux_max')
        if flux_brightest is not None:
            self.flux_brightest = flux_brightest

        if flux_avg is not None or flux_brightest is not None:
            self.update_labels()

    def update_view(self):
        if self.img is None:
            return

        if self.masked:
            img = np.ma.masked_array(self.img, mask=self.mask,
                                     fill_value=np.nan)
        else:
            img = self.img

        img_min, img_max = self.compute_min_max(img)

        self.saturation = img.max() / self.image_info['max']

        self.flux_view.setImage(img, img_min, img_max)

    def update_labels(self):
        self.flux_avg_label.updateText(
            flux_avg=self.flux_avg * self.data_scaling, unit=self.data_unit)
        self.flux_brightest_label.updateText(
            flux_brightest=self.flux_brightest * self.data_scaling,
            unit=self.data_unit)

        if self.saturation >= 1:
            self.saturation_label.setText('Saturated !')
            self.saturation_label.setStyleSheet(f'color: {Color.RED.name()};')
        else:
            self.saturation_label.updateText(saturation=self.saturation * 100)
            self.saturation_label.setStyleSheet('')

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.flux_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.flux_view.updateColormap(colormaps.BlackBodyTransparent())

    def change_mask(self, state):
        self.masked = Qt.CheckState(state) == Qt.Checked
        self.update_view()
