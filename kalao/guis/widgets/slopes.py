from typing import Any

import numpy as np

from PySide6.QtCore import Signal
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget

from compiled.ui_slopes import Ui_SlopesWidget

from kalao.common import ktools

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils import colormaps
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.widgets import KWidget

import config


class SlopesWidget(KWidget, BackendDataMixin):
    image_info = config.Images.shwfs_slopes

    saturation = np.nan
    slope_x_avg = np.nan
    slope_y_avg = np.nan
    residual_rms = np.nan

    img = None
    masked = False

    hovered = Signal(str)

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend
        self.mask = ktools.generate_slopes_mask_from_subaps(
            config.WFS.masked_subaps)

        self.ui = Ui_SlopesWidget()
        self.ui.setupUi(self)

        self.resize(600, 400)

        self.ui.minmax_widget.setup(self.ui.slopes_view, ' px', 2, 1, -99, 99,
                                    self.image_info['min'],
                                    self.image_info['max'], symetric=True)
        self.ui.slopes_view.set_data_md(' px', 2)
        self.ui.slopes_view.set_axis_md('', 0)

        self.change_units(Qt.CheckState.Unchecked)
        self.change_colormap(Qt.CheckState.Unchecked)

        self.ui.slopes_view.hovered_str.connect(lambda string: self.hovered.
                                                emit(string))
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

        img_min, img_max = self.ui.minmax_widget.compute_min_max(img)

        self.ui.slopes_view.setImage(img, img_min, img_max)

    def update_labels(self) -> None:
        self.ui.slope_x_avg_label.updateText(
            slope_x_avg=self.slope_x_avg * self.ui.slopes_view.data_scaling,
            unit=self.ui.slopes_view.data_unit,
            precision=self.ui.slopes_view.data_precision)

        self.ui.slope_y_avg_label.updateText(
            slope_y_avg=self.slope_y_avg * self.ui.slopes_view.data_scaling,
            unit=self.ui.slopes_view.data_unit,
            precision=self.ui.slopes_view.data_precision)

        self.ui.residual_rms_label.updateText(
            residual_rms=self.residual_rms * self.ui.slopes_view.data_scaling,
            unit=self.ui.slopes_view.data_unit,
            precision=self.ui.slopes_view.data_precision)

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
            self.ui.minmax_widget.update_spinboxes_unit(
                '"', 2, config.WFS.plate_scale)
            self.ui.slopes_view.set_data_md('"', 2,
                                            scaling=config.WFS.plate_scale)
        else:
            self.ui.minmax_widget.update_spinboxes_unit(' px', 2, 1)
            self.ui.slopes_view.set_data_md(' px', 2, scaling=1)

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
