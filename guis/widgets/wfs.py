import numpy as np

from PySide6.QtGui import QPen, Qt

from kalao.utils import ktools
from kalao.utils.image import LogScale

from guis.kalao import colormaps
from guis.kalao.definitions import Color
from guis.kalao.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KWidget

import config


class WFSWidget(KWidget, MinMaxMixin, SceneHoverMixin, BackendDataMixin):
    associated_stream = config.Streams.NUVU
    stream_info = config.StreamInfo.nuvu_stream

    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0

    subap_current = None
    act_current = None

    saturation = np.nan

    def __init__(self, backend, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.backend = backend

        loadUi('wfs.ui', self)
        self.resize(600, 400)

        self.init_minmax(self.wfs_view)

        self.change_colormap(Qt.Unchecked)

        if self.stream_info['shape'] == (128, 128):
            self.subaps_size = 10
            self.subaps_offset = 10
            self.subaps_pitch = 10
        elif self.stream_info['shape'] == (64, 64):
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

            pen = QPen(color, 1.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
            pen.setCosmetic(True)

            roi = self.wfs_view.scene.addRect(
                self.subaps_pitch * k + self.subaps_offset,
                self.subaps_pitch * j + self.subaps_offset, self.subaps_size,
                self.subaps_size, pen)
            roi.setZValue(1)
            self.subapertures[i] = roi

        self.actuators = {}
        for i in list(range(140)):
            j, k = ktools.get_actuator_2d(i)

            pen = QPen(Color.DARK_GREY, 1.5, Qt.SolidLine, Qt.SquareCap,
                       Qt.MiterJoin)
            pen.setCosmetic(True)

            roi = self.wfs_view.scene.addEllipse(
                self.subaps_pitch * k + self.subaps_offset - 1,
                self.subaps_pitch * j + self.subaps_offset - 1, 1, 1, pen)
            roi.setZValue(1)
            self.actuators[i] = roi

        self.wfs_view.setView(self.stream_info['shape'])

        self.wfs_view.hovered.connect(self.hover_xyv_to_str)
        backend.streams_all_updated.connect(self.streams_all_updated)

    def streams_all_updated(self, data):
        img = self.consume_stream(data, config.Streams.NUVU)

        if img is not None:
            img_min, img_max = self.compute_min_max(img)

            # Do not check min due to bias subtraction
            self.saturation = img.max() / self.stream_info['max']

            self.wfs_view.setImage(img, img_min, img_max, scale=LogScale)

            self.update_labels()

    def update_labels(self):
        if self.saturation >= 1:
            self.saturation_label.setText('Saturated !')
            self.saturation_label.setStyleSheet(f'color: {Color.RED.name()};')
        else:
            self.saturation_label.updateText(saturation=self.saturation * 100)
            self.saturation_label.setStyleSheet('')

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.wfs_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.wfs_view.updateColormap(colormaps.BlackBody())

    def hover_xyv_to_str(self, x, y, v):
        pen = QPen(Color.GREEN, 1.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        if x != -1 and y != -1:
            string = self.formatter.format(
                'X: {x:.{axis_precision}f}{axis_unit}, Y: {y:.{axis_precision}f}{axis_unit}, V: {v:.{data_precision}f}{data_unit}',
                x=(x - self.data_center_x) * self.axis_scaling,
                y=(y - self.data_center_y) * self.axis_scaling,
                v=v * self.data_scaling, axis_precision=self.axis_precision,
                axis_unit=self.axis_unit, data_precision=self.data_precision,
                data_unit=self.data_unit)

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

    def reset_subaperture_highlight(self):
        if self.subap_current is not None:
            self.subapertures[self.subap_current].setPen(
                self.subap_previous_pen)

            self.subap_current = None
            self.subap_previous_pen = None

    def reset_actuator_highlight(self):
        if self.act_current is not None:
            self.actuators[self.act_current].setPen(self.act_previous_pen)

            self.act_current = None
            self.act_previous_pen = None
