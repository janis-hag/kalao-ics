from typing import Any

import numpy as np

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget

from compiled.ui_slopes import Ui_SlopesWidget

from kalao.utils import ktools

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils import colormaps
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import (BackendDataMixin, MinMaxMixin,
                                     SceneHoverMixin)
from kalao.guis.utils.widgets import KWidget

import config


class SlopesWidget(KWidget, MinMaxMixin, SceneHoverMixin, BackendDataMixin):
    image_info = config.Images.shwfs_slopes

    data_unit = ' px'
    data_precision = 2

    axis_unit = ' px'
    axis_precision = 0

    tiptilt_unit = ' px'
    tiptilt_scaling = 1
    tiptilt_precision = 2

    saturation = np.nan
    slope_x_avg = np.nan
    slope_y_avg = np.nan
    residual_rms = np.nan

    img = None
    masked = False

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend
        self.mask = ktools.generate_slopes_mask_from_subaps(
            config.WFS.masked_subaps)

        self.ui = Ui_SlopesWidget()
        self.ui.setupUi(self)

        self.resize(600, 400)

        self.init_minmax(self.ui.slopes_view, symetric=True)

        self.change_units(Qt.CheckState.Unchecked)
        self.change_colormap(Qt.CheckState.Unchecked)

        self.ui.slopes_view.hovered.connect(self.hover_xyv_to_str)
        backend.streams_all_updated.connect(self.streams_all_updated)

    def streams_all_updated(self, data: dict[str, Any]) -> None:
        img = self.consume_shm(data, config.SHM.SLOPES)

        if img is not None:
            self.img = img
            self.update_view()

        slope_x_avg = self.consume_fps_param(data, config.FPS.SHWFS,
                                             'slope_x_avg')
        if slope_x_avg is not None:
            self.slope_x_avg = slope_x_avg

        slope_y_avg = self.consume_fps_param(data, config.FPS.SHWFS,
                                             'slope_y_avg')
        if slope_y_avg is not None:
            self.slope_y_avg = slope_y_avg

        residual_rms = self.consume_fps_param(data, config.FPS.SHWFS,
                                              'residual_rms')
        if residual_rms is not None:
            self.residual_rms = residual_rms

        if slope_x_avg is not None or slope_y_avg is not None or residual_rms is not None:
            self.update_labels()

    def update_view(self) -> None:
        if self.img is None:
            return

        if self.masked:
            img = np.ma.masked_array(self.img, mask=self.mask,
                                     fill_value=np.nan)
        else:
            img = self.img

        self.saturation = max(img.max() / self.image_info['max'],
                              img.min() / self.image_info['min'])

        img_min, img_max = self.compute_min_max(img)

        self.ui.slopes_view.setImage(img, img_min, img_max)

    def update_labels(self) -> None:
        self.ui.slope_x_avg_label.updateText(
            slope_x_avg=self.slope_x_avg * self.tiptilt_scaling,
            unit=self.tiptilt_unit, precision=self.tiptilt_precision)
        self.ui.slope_y_avg_label.updateText(
            slope_y_avg=self.slope_y_avg * self.tiptilt_scaling,
            unit=self.tiptilt_unit, precision=self.tiptilt_precision)
        self.ui.residual_rms_label.updateText(
            residual_rms=self.residual_rms * self.data_scaling,
            unit=self.data_unit, precision=self.data_precision)

        if self.saturation >= 1:
            self.ui.saturation_label.setText('Saturated !')
            self.ui.saturation_label.setStyleSheet(
                f'color: {Color.RED.name()};')
        else:
            self.ui.saturation_label.updateText(saturation=self.saturation *
                                                100)
            self.ui.saturation_label.setStyleSheet('')

    def change_units(self, state: Qt.CheckState) -> None:
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.tiptilt_scaling = config.WFS.plate_scale
            self.tiptilt_unit = '"'
            self.tiptilt_precision = 1
            self.update_spinboxes_unit('"', config.WFS.plate_scale, 1)
        else:
            self.tiptilt_scaling = 1
            self.tiptilt_unit = ' px'
            self.tiptilt_precision = 2
            self.update_spinboxes_unit(' px', 1, 2)

        self.update_labels()

    def change_colormap(self, state: Qt.CheckState) -> None:
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.ui.slopes_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.ui.slopes_view.updateColormap(colormaps.CoolWarmTransparent())

    def change_mask(self, state: Qt.CheckState) -> None:
        self.masked = Qt.CheckState(state) == Qt.CheckState.Checked
        self.update_view()
