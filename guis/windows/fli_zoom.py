import time

import numpy as np

from PySide6.QtCore import QRectF, QSignalBlocker, Slot
from PySide6.QtGui import QPen, Qt

from kalao.utils import image

from guis.kalao import colormaps
from guis.kalao.definitions import Color, Cuts, Scale
from guis.kalao.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOMainWindow

import config


class FLIZoomWindow(KalAOMainWindow, MinMaxMixin, SceneHoverMixin,
                    BackendDataMixin):
    associated_stream = config.Streams.FLI
    stream_info = config.StreamInfo.fli_stream

    data_unit = ' ADU'
    data_precision = 0
    data_center_x = config.FLI.center_x
    data_center_y = config.FLI.center_y

    axis_unit = ' px'
    axis_precision = 0
    axis_scaling = 1

    zoom_center_x = config.FLI.center_x
    zoom_center_y = config.FLI.center_y
    zoom_level = 4

    last_img = None

    tick_fontsize = 10
    tick_spacing = 10
    tick_tick_length = 10
    tick_text_spacing = 5
    ticks_pos = [-400, -300, -200, -100, 0, 100, 200, 300, 400]

    def __init__(self, backend, img, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.img = img

        loadUi('fli_zoom.ui', self)
        self.resize(800, 600)

        self.init_minmax([self.fli_view, self.zoom_view])

        self.fli_view.setView(self.stream_info['shape'])

        pen = QPen(Color.YELLOW, 1.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.roi = self.fli_view.scene.addRect(0, 0, 1024, 1024, pen)
        self.roi.setZValue(1)

        for colormap in colormaps.get_all_colormaps(exclude_transparent=True):
            self.colormap_combobox.addItem(colormap.__name__, colormap)

        for scale in Scale:
            self.scale_combobox.addItem(str(scale.value()), scale.value)

        for cuts in Cuts:
            self.cuts_combobox.addItem(str(cuts.value), cuts.value)

        self.fli_view.hovered.connect(self.hover_xyv_to_str)
        self.zoom_view.hovered.connect(self.hover_xyv_to_str_zoom)

        self.fli_view.scene.clicked.connect(self.fli_clicked)
        self.fli_view.scene.dragged.connect(self.fli_dragged)
        self.fli_view.scene.scrolled.connect(self.fli_scrolled)

        self.zoom_view.scene.clicked.connect(self.zoom_clicked)
        self.zoom_view.scene.scrolled.connect(self.zoom_scrolled)

        self.on_onsky_checkbox_stateChanged(self.onsky_checkbox.checkState())

        self.star_label.updateText(
            x=np.nan,
            y=np.nan,
            peak=np.nan,
            fwhm=np.nan,
            data_unit=self.data_unit,
            data_precision=np.nan,
            axis_unit=self.axis_unit,
            axis_precision=np.nan,
        )

        self.hovered.connect(self.info_to_statusbar)
        backend.fli_updated.connect(self.fli_updated)

        if img is not None:
            self.update_fli_view(img)

        self.show()

    def fli_updated(self, data):
        img = self.consume_stream(data, config.Streams.FLI)

        if img is not None:
            self.update_fli_view(img)

    @Slot(int)
    def on_colormap_combobox_currentIndexChanged(self, index):
        colormap = self.colormap_combobox.currentData()()
        self.fli_view.updateColormap(colormap)
        self.zoom_view.updateColormap(colormap)

    @Slot(int)
    def on_scale_combobox_currentIndexChanged(self, index):
        scale = self.scale_combobox.currentData()
        self.fli_view.updateScale(scale)
        self.zoom_view.updateScale(scale)

    @Slot(int)
    def on_cuts_combobox_currentIndexChanged(self, index):
        self.autoscale_checkbox.setChecked(True)
        self.update_fli_view(self.img)

    @Slot(int)
    def on_follow_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.zoom_center_x = self.star_x
            self.zoom_center_y = self.star_y

            self.update_zoom_view()

    def hover_xyv_to_str_zoom(self, x, y, v):
        if x != -1 and y != -1:
            x, y = self.xy_to_zoom_xy(x, y)

            string = f'X: {(x-self.data_center_x)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, Y: {(y-self.data_center_y)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, V: {v*self.data_scaling:.{self.data_precision}f}{self.data_unit}'

            self.hovered.emit(string)
        else:
            self.hovered.emit('')

    def fli_clicked(self, x, y):
        self.follow_checkbox.setChecked(False)

        if not 0 <= x < 1024 or not 0 <= y < 1024:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def fli_dragged(self, x, y, dx, dy):
        if not 0 <= x < 1024 or not 0 <= y < 1024:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def fli_scrolled(self, x, y, z):
        if not 0 <= x < 1024 or not 0 <= y < 1024:
            return

        if not self.follow_checkbox.isChecked():
            self.zoom_center_x = round(x)
            self.zoom_center_y = round(y)

        if z > 0:
            self.zoom_level *= 2

            if self.zoom_level > 128:
                self.zoom_level = 128
        else:
            self.zoom_level //= 2

            if self.zoom_level < 2:
                self.zoom_level = 2

        self.update_zoom_view()

    def zoom_clicked(self, x, y):
        self.follow_checkbox.setChecked(False)

        x, y = self.xy_to_zoom_xy(x, y)

        if not 0 <= x < 1024 or not 0 <= y < 1024:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def zoom_scrolled(self, x, y, z):
        hw = 1024 // self.zoom_level // 2

        fx = (x - self.view_shift_x) / hw - 1
        fy = (y - self.view_shift_y) / hw - 1

        x, y = self.xy_to_zoom_xy(x, y)

        if not 0 <= x < 1024 or not 0 <= y < 1024:
            return

        if z > 0:
            self.zoom_level *= 2

            if self.zoom_level > 128:
                self.zoom_level = 128

            elif not self.follow_checkbox.isChecked():
                self.zoom_center_x = round(x - fx*hw/2)
                self.zoom_center_y = round(y - fy*hw/2)

        else:
            self.zoom_level //= 2

            if self.zoom_level < 2:
                self.zoom_level = 2

            elif not self.follow_checkbox.isChecked():
                self.zoom_center_x = round(x - fx*hw*2)
                self.zoom_center_y = round(y - fy*hw*2)

        self.update_zoom_view()

    def xy_to_zoom_xy(self, x, y):
        return self.zoom_center_x - 1024 // self.zoom_level // 2 + x - self.view_shift_x, self.zoom_center_y - 1024 // self.zoom_level // 2 + y - self.view_shift_y

    def update_fli_view(self, img):
        self.img = img

        img_min, img_max = self.compute_min_max(
            self.img, self.cuts_combobox.currentData())

        self.fli_view.setImage(self.img, img_min, img_max,
                               self.scale_combobox.currentData())

        self.star_x, self.star_y, self.star_peak, self.star_fwhm = self.find_star_fast(self.img)

        self.star_label.updateText(
            x=(self.star_x - self.data_center_x) * self.axis_scaling,
            y=(self.star_y - self.data_center_y) * self.axis_scaling,
            peak=self.star_peak * self.data_scaling, fwhm=self.star_fwhm * self.axis_scaling,
            data_unit=self.data_unit, data_precision=self.data_precision,
            axis_unit=self.axis_unit, axis_precision=self.axis_precision + 1)

        if self.follow_checkbox.isChecked():
            self.zoom_center_x = self.star_x
            self.zoom_center_y = self.star_y

        self.update_zoom_view()

    def update_zoom_view(self):
        x = self.zoom_center_x
        y = self.zoom_center_y
        hw = 1024 // self.zoom_level // 2

        with QSignalBlocker(self.x_spinbox):
            self.x_spinbox.setValue(x - self.data_center_x)

        with QSignalBlocker(self.y_spinbox):
            self.y_spinbox.setValue(y - self.data_center_y)

        with QSignalBlocker(self.zoom_spinbox):
            self.zoom_spinbox.setValue(self.zoom_level)

        self.roi.setRect(x - hw, y - hw, 2 * hw, 2 * hw)

        zoom = image.cut(self.img, 2 * hw, [y, x], overflow='cut')

        if x - hw < 0:
            self.view_shift_x = zoom.shape[1] - 2*hw
        else:
            self.view_shift_x = 0

        if y - hw < 0:
            self.view_shift_y = zoom.shape[0] - 2*hw
        else:
            self.view_shift_y = 0

        self.zoom_view.margins = np.array(
            self.fli_view.margins) / self.zoom_level

        self.zoom_view.setImage(
            zoom, self.min_spinbox.value(), self.max_spinbox.value(),
            self.scale_combobox.currentData(),
            view=QRectF(self.view_shift_x, self.view_shift_y, 2 * hw, 2 * hw))

    def find_star_fast(self, img):
        start = time.monotonic()
        psf_bb = 25

        y, x = np.unravel_index(np.argmax(img, axis=None), img.shape)
        peak = img[y, x]

        background = np.median(img)

        box = img[y - psf_bb:y + psf_bb, x - psf_bb:x + psf_bb] - background

        circle = (2 * box > box.max()).sum()
        if circle == 0:
            fwhm = np.nan
        else:
            fwhm = 2 * np.sqrt(circle / np.pi)

        return x, y, peak, fwhm

    @Slot(int)
    def on_onsky_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.axis_scaling = config.FLI.plate_scale
            self.axis_unit = ' asec'
            self.axis_precision = 1
        else:
            self.axis_scaling = 1
            self.axis_unit = ' px'
            self.axis_precision = 0

        ticks_x = []
        ticks_y = []
        for xy in [-400, -300, -200, -100, 0, 100, 200, 300, 400]:
            tick_label = f'{xy*self.axis_scaling:.{self.axis_precision}f}'
            tick_pos_x = xy + self.data_center_x
            tick_pos_y = xy + self.data_center_y

            ticks_x.append((tick_pos_x, tick_label))
            ticks_y.append((tick_pos_y, tick_label))

        self.fli_view.addTicks(self.tick_spacing, self.tick_tick_length,
                               self.tick_text_spacing, self.tick_fontsize,
                               ticks_x, ticks_y)
        self.fli_view.addTicksLabels(self.tick_spacing, self.tick_tick_length,
                                     self.tick_text_spacing,
                                     self.tick_fontsize, ticks_x, ticks_y)

    def closeEvent(self, event):
        self.backend.fli_updated.disconnect(self.fli_updated)
        event.accept()

    def showEvent(self, event):
        self.backend.fli_updated.connect(self.fli_updated)
        event.accept()
