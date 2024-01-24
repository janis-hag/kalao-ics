import numpy as np

from PySide6.QtGui import Qt

from kalao.utils import ktools

from guis.utils import colormaps
from guis.utils.definitions import Color
from guis.utils.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KWidget

import config


class SlopesWidget(KWidget, MinMaxMixin, SceneHoverMixin, BackendDataMixin):
    associated_stream = config.Streams.SLOPES
    stream_info = config.StreamInfo.shwfs_slopes

    data_unit = ' px'
    data_precision = 2

    axis_unit = ' px'
    axis_precision = 0

    saturation = np.nan
    slope_x_avg = np.nan
    slope_y_avg = np.nan
    residual_rms = np.nan

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.mask = ktools.generate_slopes_mask_from_subaps(
            config.WFS.masked_subaps)

        loadUi('slopes.ui', self)
        self.resize(600, 400)

        self.init_minmax(self.slopes_view, symetric=True)

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        self.slopes_view.hovered.connect(self.hover_xyv_to_str)
        backend.streams_all_updated.connect(self.streams_all_updated)

    def streams_all_updated(self, data):
        img = self.consume_stream(data, config.Streams.SLOPES)

        if img is not None:
            img = np.ma.masked_array(img, mask=self.mask, fill_value=np.nan)

            self.saturation = max(img.max() / self.stream_info['max'],
                                  img.min() / self.stream_info['min'])

            img_min, img_max = self.compute_min_max(img)

            self.slopes_view.setImage(img, img_min, img_max)

        slope_x_avg = self.consume_param(data, config.FPS.SHWFS, 'slope_x_avg')
        if slope_x_avg is not None:
            self.slope_x_avg = slope_x_avg

        slope_y_avg = self.consume_param(data, config.FPS.SHWFS, 'slope_y_avg')
        if slope_y_avg is not None:
            self.slope_y_avg = slope_y_avg

        residual_rms = self.consume_param(data, config.FPS.SHWFS,
                                          'residual_rms')
        if residual_rms is not None:
            self.residual_rms = residual_rms

        if slope_x_avg is not None or slope_y_avg is not None or residual_rms is not None:
            self.update_labels()

    def update_labels(self):
        self.slope_x_avg_label.updateText(
            slope_x_avg=self.slope_x_avg * self.data_scaling,
            unit=self.data_unit)
        self.slope_y_avg_label.updateText(
            slope_y_avg=self.slope_y_avg * self.data_scaling,
            unit=self.data_unit)
        self.residual_rms_label.updateText(
            residual_rms=self.residual_rms * self.data_scaling,
            unit=self.data_unit)

        if self.saturation >= 1:
            self.saturation_label.setText('Saturated !')
            self.saturation_label.setStyleSheet(f'color: {Color.RED.name()};')
        else:
            self.saturation_label.updateText(saturation=self.saturation * 100)
            self.saturation_label.setStyleSheet('')

    def change_units(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.update_spinboxes_unit('"', config.WFS.plate_scale, 2)
        else:
            self.update_spinboxes_unit(' px', 1, 2)

        self.update_labels()

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.slopes_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.slopes_view.updateColormap(colormaps.CoolWarmTransparent())
