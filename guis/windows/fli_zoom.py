import numpy as np

from PySide6.QtCore import QPointF, QRectF, QSignalBlocker, Slot
from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import QMessageBox

from kalao.utils import image, starfinder

from guis.kalao import colormaps
from guis.kalao.definitions import Color, Cuts, Scale
from guis.kalao.mixins import (BackendActionMixin, BackendDataMixin,
                               MinMaxMixin, SceneHoverMixin)
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KMainWindow

from kalao.definitions.enums import StrEnum

import config


def find_star_fast(img, psf_bb=25):
    y, x = np.unravel_index(np.argmax(img, axis=None), img.shape)
    background = np.median(img)

    peak = img[y, x] - background

    box = img[y - psf_bb:y + psf_bb, x - psf_bb:x + psf_bb] - background

    circle = (2 * box > box.max()).sum()
    if circle == 0:
        fwhm = np.nan
    else:
        fwhm = 2 * np.sqrt(circle / np.pi)

    return x, y, peak, fwhm


class FollowMode(StrEnum):
    FIXED = 'Fixed'
    MOUSE = 'Follow mouse'
    STAR = 'Follow star'


class FLIZoomWindow(KMainWindow, BackendActionMixin, MinMaxMixin,
                    SceneHoverMixin, BackendDataMixin):
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
    zoom_level = 16
    zoom_min = 2
    zoom_max = 128

    last_img = None

    tick_fontsize = 10
    tick_spacing = 10
    tick_tick_length = 10
    tick_text_spacing = 5
    ticks_pos = [-400, -300, -200, -100, 0, 100, 200, 300, 400]

    saturation = np.nan
    star_x = np.nan
    star_y = np.nan
    star_peak = np.nan
    star_fwhm = np.nan

    centering = False

    WFS_fov = 4 * config.WFS.plate_scale / config.FLI.plate_scale

    def __init__(self, backend, img, on_sky_unit=False, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.img = img

        loadUi('fli_zoom.ui', self)
        self.resize(1400, 600)

        self.init_minmax([self.fli_view, self.zoom_view])

        self.fli_view.setView(self.stream_info['shape'])

        pen = QPen(Color.YELLOW, 1.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.zoom_window = self.fli_view.scene.addRect(0, 0, 1024, 1024, pen)
        self.zoom_window.setZValue(1)

        pen = QPen(Color.BLUE, 1.5, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.wfs_fov = self.fli_view.scene.addEllipse(
            self.data_center_x - self.WFS_fov / 2, self.data_center_y -
            self.WFS_fov / 2, self.WFS_fov, self.WFS_fov, pen)
        self.wfs_fov.setZValue(1)
        self.wfs_fov.setVisible(False)

        pen = QPen(Color.GREEN, 1.5, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.vertical_line = self.fli_view.scene.addLine(
            512, 0, 512, 1024, pen)
        self.vertical_line.setZValue(1)
        self.vertical_line.setVisible(False)

        self.horizontal_line = self.fli_view.scene.addLine(
            0, 512, 1024, 512, pen)
        self.horizontal_line.setZValue(1)
        self.horizontal_line.setVisible(False)

        self.zoom_vertical_line = self.zoom_view.scene.addLine(
            512, 0, 512, 1024, pen)
        self.zoom_vertical_line.setZValue(1)
        self.zoom_vertical_line.setVisible(False)

        self.zoom_horizontal_line = self.zoom_view.scene.addLine(
            0, 512, 1024, 512, pen)
        self.zoom_horizontal_line.setZValue(1)
        self.zoom_horizontal_line.setVisible(False)

        for colormap in colormaps.get_all_colormaps(exclude_transparent=True):
            self.colormap_combobox.addItem(colormap.__name__, colormap)

        for scale in Scale:
            self.scale_combobox.addItem(str(scale.value()), scale.value)

        self.cuts_combobox.addItem('Min – Max w/o hot pixels', None)
        for cuts in Cuts:
            self.cuts_combobox.addItem(str(cuts.value), cuts.value)

        for mode in FollowMode:
            self.window_combobox.addItem(mode.value, mode.value)

        self.fli_view.hovered.connect(self.hover_xyv_to_str_fli)
        self.zoom_view.hovered.connect(self.hover_xyv_to_str_zoom)

        self.fli_view.scene.clicked.connect(self.fli_clicked)
        self.fli_view.scene.dragged.connect(self.fli_dragged)
        self.fli_view.scene.scrolled.connect(self.fli_scrolled)

        self.zoom_view.scene.clicked.connect(self.zoom_clicked)
        self.zoom_view.scene.scrolled.connect(self.zoom_scrolled)

        self.onsky_checkbox.setChecked(on_sky_unit)
        self.on_onsky_checkbox_stateChanged(self.onsky_checkbox.checkState())

        self.hovered.connect(self.info_to_statusbar)
        backend.fli_updated.connect(self.fli_updated, Qt.UniqueConnection)

        if img is not None:
            self.update_fli_view(img)

        self.show()
        self.center()

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
    def on_window_combobox_currentIndexChanged(self, index):
        if self.window_combobox.currentData() == FollowMode.STAR:
            self.update_zoom_view()

    @Slot(bool)
    def on_centering_button_clicked(self, checked=None):
        if self.centering:
            self.exit_manual_centering()
        else:
            self.enter_manual_centering(show_help=False)

    def enter_manual_centering(self, show_help=True):
        if not self.centering:
            self.centering = True

            self.wfs_fov.setVisible(True)

            self.zoom_vertical_line.setVisible(True)
            self.zoom_horizontal_line.setVisible(True)

            self.window_combobox.setCurrentIndex(
                self.window_combobox.findData(FollowMode.MOUSE))
            self.window_combobox.setEnabled(False)

            self.zoom_level = 16

            self.update_zoom_view()

            self.centering_button.setText('Validate Manual Centering')

            if True:
                msgbox = QMessageBox(self)
                msgbox.setIcon(QMessageBox.Information)
                msgbox.setText("<b>Manual centering needed!</b>")
                msgbox.setInformativeText(
                    'Manual centering has been requested. Click on a star to center it. Validate using the "Validate Manual Centering" button.'
                )
                msgbox.setModal(False)
                msgbox.show()

    def exit_manual_centering(self):
        if self.centering:
            self.centering = False

            self.wfs_fov.setVisible(False)

            self.zoom_vertical_line.setVisible(False)
            self.zoom_horizontal_line.setVisible(False)

            self.window_combobox.setCurrentIndex(
                self.window_combobox.findData(FollowMode.FIXED))
            self.window_combobox.setEnabled(True)

            self.zoom_center_x = self.data_center_x
            self.zoom_center_y = self.data_center_y

            self.update_zoom_view()

            self.centering_button.setText('Enter Manual Centering')

            self.action_send(self.centering_button,
                             self.backend.get_centering_validate)

    def hover_xyv_to_str_fli(self, x, y, v):
        if x != -1 and y != -1:
            if self.window_combobox.currentData() == FollowMode.MOUSE:
                self.zoom_center_x = x
                self.zoom_center_y = y

                self.update_zoom_view()

            if self.centering:
                self.vertical_line.setLine(x, 0, x, 1024)
                self.horizontal_line.setLine(0, y, 1024, y)

                self.vertical_line.setVisible(True)
                self.horizontal_line.setVisible(True)

            string = f'X: {(x-self.data_center_x)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, Y: {(y-self.data_center_y)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, V: {v*self.data_scaling:.{self.data_precision}f}{self.data_unit}'

            self.hovered.emit(string)
        else:
            if self.window_combobox.currentData() == FollowMode.MOUSE:
                self.zoom_center_x = self.data_center_x
                self.zoom_center_y = self.data_center_y

                self.update_zoom_view()

            if self.centering:
                self.vertical_line.setVisible(False)
                self.horizontal_line.setVisible(False)

            self.hovered.emit('')

    def hover_xyv_to_str_zoom(self, x, y, v):
        if x != -1 and y != -1:
            string = f'X: {(x-self.data_center_x)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, Y: {(y-self.data_center_y)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, V: {v*self.data_scaling:.{self.data_precision}f}{self.data_unit}'

            self.hovered.emit(string)
        else:
            self.hovered.emit('')

    def fli_clicked(self, x, y):
        if not 0 <= x < 1024 or not 0 <= y < 1024:
            return

        if self.centering:
            self.action_send([], self.backend.set_centering_manual, x, y)

        if self.window_combobox.currentData() != FollowMode.FIXED:
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

        if self.window_combobox.currentData() == FollowMode.FIXED:
            self.zoom_center_x = round(x)
            self.zoom_center_y = round(y)

        if z > 0:
            self.zoom_level *= 2

            if self.zoom_level > self.zoom_max:
                self.zoom_level = self.zoom_max
        else:
            self.zoom_level //= 2

            if self.zoom_level < self.zoom_min:
                self.zoom_level = self.zoom_min

        self.update_zoom_view()

    def zoom_clicked(self, x, y):
        if self.window_combobox.currentData() != FollowMode.FIXED:
            return

        if not 0 <= x < 1024 or not 0 <= y < 1024:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def zoom_scrolled(self, x, y, z):
        hw = 1024 // self.zoom_level // 2

        fx = (x - self.zoom_center_x) / hw
        fy = (y - self.zoom_center_y) / hw

        if not 0 <= x < 1024 or not 0 <= y < 1024:
            return

        if z > 0:
            self.zoom_level *= 2

            if self.zoom_level > self.zoom_max:
                self.zoom_level = self.zoom_max

            elif self.window_combobox.currentData() == FollowMode.FIXED:
                self.zoom_center_x = round(x - fx*hw/2)
                self.zoom_center_y = round(y - fy*hw/2)

        else:
            self.zoom_level //= 2

            if self.zoom_level < self.zoom_min:
                self.zoom_level = self.zoom_min

            elif self.window_combobox.currentData() == FollowMode.FIXED:
                self.zoom_center_x = round(x - fx*hw*2)
                self.zoom_center_y = round(y - fy*hw*2)

        self.update_zoom_view()

    def update_fli_view(self, img):
        if img is None:
            return

        self.img = img

        stars, bad_pixels = starfinder.find_stars_and_bad_pixels(
            self.img, num=1)

        if len(stars) == 0:
            self.star_x = np.nan
            self.star_y = np.nan
            self.star_peak = np.nan
            self.star_fwhm = np.nan
        else:
            self.star_x, self.star_y, self.star_peak, self.star_fwhm = stars[0]

        if self.cuts_combobox.currentIndex == 0:
            img_nan = img.copy()
            img_nan[bad_pixels] = np.nan
            img_min = np.nanmin(img_nan)
            img_max = np.nanmax(img_nan)

            if self.autoscale_checkbox.isChecked():
                with QSignalBlocker(self.min_spinbox):
                    self.min_spinbox.setMaximum(img_max)
                    self.min_spinbox.setValue(img_min)

                with QSignalBlocker(self.max_spinbox):
                    self.max_spinbox.setMinimum(img_min)
                    self.max_spinbox.setValue(img_max)
        else:
            img_min, img_max = self.compute_min_max(
                self.img, self.cuts_combobox.currentData())

        self.saturation = img.max() / self.stream_info['max']

        self.fli_view.setImage(self.img, img_min, img_max,
                               self.scale_combobox.currentData())

        #self.fli_view.addNEIndicator(parang from keywords)

        self.update_labels()
        self.update_zoom_view()

    def update_zoom_view(self):
        if self.window_combobox.currentData(
        ) == FollowMode.STAR and not np.isnan([self.star_x, self.star_y
                                               ]).any():
            self.zoom_center_x = round(self.star_x)
            self.zoom_center_y = round(self.star_y)

        x = self.zoom_center_x
        y = self.zoom_center_y
        hw = 1024 // self.zoom_level // 2

        with QSignalBlocker(self.x_spinbox):
            self.x_spinbox.setValue(x - self.data_center_x)

        with QSignalBlocker(self.y_spinbox):
            self.y_spinbox.setValue(y - self.data_center_y)

        with QSignalBlocker(self.zoom_spinbox):
            self.zoom_spinbox.setValue(self.zoom_level)
            self.update_zoom_spinbox_suffix()

        self.zoom_window.setRect(x - hw, y - hw, 2 * hw, 2 * hw)
        self.zoom_vertical_line.setLine(x, y - hw, x, y + hw)
        self.zoom_horizontal_line.setLine(x - hw, y, x + hw, y)

        zoom = image.cut(self.img, 2 * hw, [y, x], overflow='cut')

        offset_x = max(x - hw, 0)
        offset_y = max(y - hw, 0)

        self.zoom_view.margins = np.array(
            self.fli_view.margins) / self.zoom_level

        self.zoom_view.setImage(zoom, self.min_spinbox.value(),
                                self.max_spinbox.value(),
                                self.scale_combobox.currentData(),
                                view=QRectF(x - hw, y - hw, 2 * hw, 2 * hw),
                                offset=QPointF(offset_x, offset_y))

    def update_labels(self):
        self.star_x_label.updateText(
            x=(self.star_x - self.data_center_x) * self.axis_scaling,
            axis_unit=self.axis_unit,
            axis_precision=self.axis_precision + 1,
        )

        self.star_y_label.updateText(
            y=(self.star_y - self.data_center_y) * self.axis_scaling,
            axis_unit=self.axis_unit,
            axis_precision=self.axis_precision + 1,
        )

        self.star_fwhm_label.updateText(
            fwhm=self.star_fwhm * self.axis_scaling,
            axis_unit=self.axis_unit,
            axis_precision=self.axis_precision + 1,
        )

        self.star_peak_label.updateText(
            peak=self.star_peak * self.data_scaling,
            data_unit=self.data_unit,
            data_precision=self.data_precision,
        )

        if self.saturation >= 1:
            self.saturation_label.setText('Saturated !')
            self.saturation_label.setStyleSheet(f'color: {Color.RED.name()};')
        else:
            self.saturation_label.updateText(saturation=self.saturation * 100)
            self.saturation_label.setStyleSheet('')

    def update_zoom_spinbox_suffix(self):
        size = 1024 // self.zoom_level * self.axis_scaling
        self.zoom_spinbox.setSuffix(
            f'x ({size:.{self.axis_precision}f}{self.axis_unit} x {size:.{self.axis_precision}f}{self.axis_unit})'
        )

    @Slot(int)
    def on_onsky_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.axis_scaling = config.FLI.plate_scale
            self.axis_unit = '"'
            self.axis_precision = 1
        else:
            self.axis_scaling = 1
            self.axis_unit = ' px'
            self.axis_precision = 0

        self.update_labels()
        self.update_zoom_spinbox_suffix()

        self.x_spinbox.setScale(self.axis_scaling, self.axis_precision)
        self.y_spinbox.setScale(self.axis_scaling, self.axis_precision)
        self.x_spinbox.setSuffix(self.axis_unit)
        self.y_spinbox.setSuffix(self.axis_unit)

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
        self.backend.fli_updated.connect(self.fli_updated, Qt.UniqueConnection)
        event.accept()
