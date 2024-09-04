from typing import Any

import numpy as np

from PySide6.QtCore import Signal
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget

from compiled.ui_flux import Ui_FluxWidget

from kalao.common import ktools

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils import colormaps
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.widgets import KWidget

import config


class FluxWidget(KWidget, BackendDataMixin):
    image_info = config.Images.shwfs_flux

    saturation = np.nan
    flux_avg = np.nan
    flux_brightest = np.nan

    img = None
    masked = False

    hovered = Signal(str)

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend
        self.mask = ktools.generate_flux_mask_from_subaps(
            config.WFS.masked_subaps)

        self.ui = Ui_FluxWidget()
        self.ui.setupUi(self)

        self.resize(600, 400)

        self.ui.minmax_widget.setup(self.ui.flux_view, ' ADU', 0, 1, -999999,
                                    999999, self.image_info['min'],
                                    self.image_info['max'])
        self.ui.flux_view.set_data_md(' ADU', 0)
        self.ui.flux_view.set_axis_md('', 0)

        self.update_labels()
        self.change_colormap(Qt.CheckState.Unchecked)

        self.ui.flux_view.hovered_str.connect(lambda string: self.hovered.emit(
            string))
        backend.streams_all_updated.connect(self.streams_all_updated)

    def streams_all_updated(self, data: dict[str, Any]) -> None:
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

    def update_view(self) -> None:
        if self.img is None:
            return

        if self.masked:
            img = np.ma.masked_array(self.img, mask=self.mask,
                                     fill_value=np.nan)
        else:
            img = self.img

        img_min, img_max = self.ui.minmax_widget.compute_min_max(img)

        self.saturation = img.max() / self.image_info['max']

        self.ui.flux_view.setImage(img, img_min, img_max)

    def update_labels(self) -> None:
        self.ui.flux_avg_label.updateText(
            flux_avg=self.flux_avg * self.ui.flux_view.data_scaling,
            unit=self.ui.flux_view.data_unit)
        self.ui.flux_brightest_label.updateText(
            flux_brightest=self.flux_brightest *
            self.ui.flux_view.data_scaling, unit=self.ui.flux_view.data_unit)

        if self.saturation >= 1:
            self.ui.saturation_label.setText('Saturated !')
            self.ui.saturation_label.setStyleSheet(
                f'color: {Color.RED.name()};')
        else:
            self.ui.saturation_label.updateText(saturation=self.saturation *
                                                100)
            self.ui.saturation_label.setStyleSheet('')

    def change_colormap(self, state: Qt.CheckState) -> None:
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.ui.flux_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.ui.flux_view.updateColormap(colormaps.BlackBodyTransparent())

    def change_mask(self, state: Qt.CheckState) -> None:
        self.masked = Qt.CheckState(state) == Qt.CheckState.Checked
        self.update_view()
