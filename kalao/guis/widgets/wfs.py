from typing import Any

import numpy as np

from PySide6.QtCore import Signal
from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import QWidget

from compiled.ui_wfs import Ui_WFSWidget

from kalao.common import ktools
from kalao.common.image import LogScale

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils import colormaps
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.string_formatter import KalAOFormatter
from kalao.guis.utils.widgets import KWidget

import config


class WFSWidget(KWidget, BackendDataMixin):
    image_info = config.Images.nuvu_stream

    subap_current = None
    act_current = None

    saturation = np.nan

    formatter = KalAOFormatter()

    hovered = Signal(str)

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent=parent)

        self.backend = backend

        self.ui = Ui_WFSWidget()
        self.ui.setupUi(self)

        self.resize(600, 400)

        self.ui.minmax_widget.setup(self.ui.wfs_view, ' ADU', 0, 1, -999999,
                                    999999, self.image_info['min'],
                                    self.image_info['max'])
        self.ui.wfs_view.set_data_md(' ADU', 0)
        self.ui.wfs_view.set_axis_md(' px', 0)

        self.change_colormap(Qt.CheckState.Unchecked)

        if self.image_info['shape'] == (128, 128):
            self.subaps_size = 10
            self.subaps_offset = 10
            self.subaps_pitch = 10
        elif self.image_info['shape'] == (64, 64):
            self.subaps_size = 4
            self.subaps_offset = 5
            self.subaps_pitch = 5

        # Add grid to window
        self.subapertures = {}
        for i in config.WFS.all_subaps:
            j, k = ktools.get_subaperture_2d(i)

            if i in config.WFS.masked_subaps:
                color = Color.DARK_GREY
            else:
                color = Color.BLUE

            pen = QPen(color, 1.5, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
            pen.setCosmetic(True)

            roi = self.ui.wfs_view.scene().addRect(
                self.subaps_pitch * k + self.subaps_offset,
                self.subaps_pitch * j + self.subaps_offset, self.subaps_size,
                self.subaps_size, pen)
            roi.setZValue(1)
            self.subapertures[i] = roi

        self.actuators = {}
        for i in list(range(140)):
            j, k = ktools.get_actuator_2d(i)

            pen = QPen(Color.DARK_GREY, 1.5, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
            pen.setCosmetic(True)

            roi = self.ui.wfs_view.scene().addEllipse(
                self.subaps_pitch * k + self.subaps_offset - 1,
                self.subaps_pitch * j + self.subaps_offset - 1, 1, 1, pen)
            roi.setZValue(1)
            self.actuators[i] = roi

        self.ui.wfs_view.setView(self.image_info['shape'])

        self.ui.wfs_view.hovered.connect(self.hover_xyv_to_str)
        backend.streams_all_updated.connect(self.streams_all_updated)

    def streams_all_updated(self, data: dict[str, Any]) -> None:
        img = self.consume_shm(data, config.SHM.NUVU)

        if img is not None:
            img_min, img_max = self.ui.minmax_widget.compute_min_max(img)

            # Do not check min due to bias subtraction
            self.saturation = img.max() / self.image_info['max']

            self.ui.wfs_view.setImage(img, img_min, img_max, scale=LogScale)

            self.update_labels()

    def update_labels(self) -> None:
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
            self.ui.wfs_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.ui.wfs_view.updateColormap(colormaps.BlackBody())

    def hover_xyv_to_str(self, x: float, y: float, v: float) -> None:
        pen = QPen(Color.GREEN, 1.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        if not np.isnan(x) and not np.isnan(y):
            x = int(x)
            y = int(y)

            string = self.formatter.format(
                'X: {x:.{axis_precision}f}{axis_unit}, Y: {y:.{axis_precision}f}{axis_unit}, V: {v:.{data_precision}f}{data_unit}',
                x=(x - self.ui.wfs_view.axis_x_offset) *
                self.ui.wfs_view.axis_scaling,
                y=(y - self.ui.wfs_view.axis_y_offset) *
                self.ui.wfs_view.axis_scaling,
                v=v * self.ui.wfs_view.data_scaling,
                axis_precision=self.ui.wfs_view.axis_precision,
                axis_unit=self.ui.wfs_view.axis_unit,
                data_precision=self.ui.wfs_view.data_precision,
                data_unit=self.ui.wfs_view.data_unit)

            subaperture = ktools.subaperture_at_px(x, y)
            actuator = ktools.actuator_at_px(x, y)

            if subaperture != self.subap_current:
                self.reset_subaperture_highlight()

                if subaperture is not None:
                    self.subap_current = subaperture
                    self.subap_previous_pen = self.subapertures[
                        subaperture].pen()
                    self.subapertures[subaperture].setPen(pen)

            if actuator != self.act_current:
                self.reset_actuator_highlight()

                if actuator is not None:
                    self.act_current = actuator
                    self.act_previous_pen = self.actuators[actuator].pen()
                    self.actuators[actuator].setPen(pen)

            if subaperture is not None:
                self.hovered.emit(f'Subaperture: {subaperture}, ' + string)
            elif actuator is not None:
                self.hovered.emit(f'Actuator: {actuator}, ' + string)
            else:
                self.reset_subaperture_highlight()
                self.reset_actuator_highlight()
                self.hovered.emit(string)
        else:
            self.reset_subaperture_highlight()
            self.reset_actuator_highlight()
            self.hovered.emit('')

    def reset_subaperture_highlight(self) -> None:
        if self.subap_current is not None:
            self.subapertures[self.subap_current].setPen(
                self.subap_previous_pen)

            self.subap_current = None
            self.subap_previous_pen = None

    def reset_actuator_highlight(self) -> None:
        if self.act_current is not None:
            self.actuators[self.act_current].setPen(self.act_previous_pen)

            self.act_current = None
            self.act_previous_pen = None
