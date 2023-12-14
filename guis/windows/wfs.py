from PySide6.QtGui import QPen, Qt

from kalao.utils import kalao_tools

from guis.kalao import colormaps
from guis.kalao.definitions import Color
from guis.kalao.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

import config


class WFSWidget(KalAOWidget, MinMaxMixin, SceneHoverMixin, BackendDataMixin):
    associated_stream = config.Streams.NUVU
    stream_info = config.StreamInfo.nuvu_stream

    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0

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
        self.rois = {}
        for i in config.AO.all_subaps:
            j, k = kalao_tools.get_subaperture_2d(i)

            if i in config.AO.masked_subaps:
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
            self.rois[i] = roi

        self.wfs_view.setView(self.stream_info['shape'])

        self.wfs_view.hovered.connect(self.hover_xyv_to_str)
        backend.streams_updated.connect(self.streams_updated)

    def streams_updated(self, data):
        img = self.consume_stream(data, config.Streams.NUVU)

        if img is not None:
            img_min, img_max = self.compute_min_max(img)

            self.wfs_view.setImage(img, img_min, img_max)

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.wfs_view.updateColormap(colormaps.GrayscaleSaturation())
        else:
            self.wfs_view.updateColormap(colormaps.BlackBody())

    subap_current = None

    def hover_xyv_to_str(self, x, y, v):
        pen = QPen(Color.GREEN, 1.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        if x != -1 and y != -1:
            string = f'X: {(x-self.data_center_x)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, Y: {(y-self.data_center_y)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, V: {v:.{self.data_precision}f}{self.data_unit}'

            subap = kalao_tools.subap_at_px(x, y)
            if subap is not None:
                self.reset_subap_color()

                self.subap_current = subap
                self.subap_previous_pen = self.rois[subap].pen()
                self.rois[subap].setPen(pen)

                #i,j = kalao_tools.get_subaperture_2d(subap)
            else:
                self.reset_subap_color()

            self.hovered.emit(string)
        else:
            self.reset_subap_color()

            self.hovered.emit('')

    def reset_subap_color(self):
        if self.subap_current is not None:
            self.rois[self.subap_current].setPen(self.subap_previous_pen)

            self.subap_current = None
            self.subap_previous_pen = None
