import math
from datetime import datetime, timezone
from enum import StrEnum

import numpy as np

from astropy.io import fits

from PySide6.QtCore import QMarginsF, QPointF, QRectF, QSignalBlocker, Slot
from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import QMessageBox

from kalao.utils import image, starfinder

from guis.utils import colormaps
from guis.utils.definitions import Color, Cuts, Scale
from guis.utils.mixins import (BackendActionMixin, BackendDataMixin,
                               MinMaxMixin, SceneHoverMixin)
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KMainWindow, KMessageBox

import config


class FollowMode(StrEnum):
    FIXED = 'Fixed'
    MOUSE = 'Follow mouse'
    STAR = 'Follow star'


class FLIZoomWindow(KMainWindow, BackendActionMixin, MinMaxMixin,
                    SceneHoverMixin, BackendDataMixin):
    associated_stream = config.Streams.FLI
    image_info = config.Images.fli

    data_unit = ' ADU'
    data_precision = 0
    data_center_x = config.FLI.center_x
    data_center_y = config.FLI.center_y

    axis_unit = ' px'
    axis_precision = 0
    axis_scaling = 1

    img_width = np.nan
    img_height = np.nan

    zoom_center_x = config.FLI.center_x
    zoom_center_y = config.FLI.center_y
    zoom_half_width = np.nan
    zoom_half_height = np.nan
    zoom_level = 16
    zoom_min = 2
    zoom_max = 128

    last_img = None

    saturation = np.nan
    timestamp = None
    star_x = np.nan
    star_y = np.nan
    star_peak = np.nan
    star_fwhm = np.nan

    centering = False
    centering_requested_by_user = False

    WFS_fov = 4 * config.WFS.plate_scale / config.FLI.plate_scale

    def __init__(self, backend, hdul=None, file=None, on_sky_unit=False,
                 parent=None):
        super().__init__(parent)

        self.backend = backend
        self.hdul = hdul
        self.file = file

        loadUi('fli_zoom.ui', self)
        self.resize(1400, 600)

        self.init_minmax([self.fli_view, self.zoom_view])

        self.fli_view.setView(self.image_info['shape'])

        self.zoom_view.margins = self.fli_view.margins = QMarginsF(
            40, 30, 40, 30)

        pen = QPen(Color.YELLOW, 1.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.zoom_window = self.fli_view.scene.addRect(-1, -1, 0, 0, pen)
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

        self.vertical_line = self.fli_view.scene.addLine(-1, -1, 0, 0, pen)
        self.vertical_line.setZValue(1)
        self.vertical_line.setVisible(False)

        self.horizontal_line = self.fli_view.scene.addLine(-1, -1, 0, 0, pen)
        self.horizontal_line.setZValue(1)
        self.horizontal_line.setVisible(False)

        self.zoom_vertical_line = self.zoom_view.scene.addLine(
            -1, -1, 0, 0, pen)
        self.zoom_vertical_line.setZValue(1)
        self.zoom_vertical_line.setVisible(False)

        self.zoom_horizontal_line = self.zoom_view.scene.addLine(
            -1, -1, 0, 0, pen)
        self.zoom_horizontal_line.setZValue(1)
        self.zoom_horizontal_line.setVisible(False)

        self.stars_itemgroup = self.fli_view.scene.createItemGroup([])

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

        if self.file is None:
            backend.fli_image_updated.connect(self.fli_image_updated,
                                              Qt.UniqueConnection)
        else:
            self.setWindowTitle(f'{self.file.name} - {self.windowTitle()}')
            hdul = fits.open(self.file)

        if hdul is not None:
            self.update_image(hdul)

        self.show()
        self.center()

    def fli_image_updated(self, data):
        hdul = self.consume_fits_full(data, config.FITS.last_image_all)

        if hdul is not None:
            self.update_image(hdul)

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
        self.update_fli_view()

    @Slot(int)
    def on_window_combobox_currentIndexChanged(self, index):
        if self.window_combobox.currentData() == FollowMode.STAR:
            self.update_zoom_view()

    @Slot(int)
    def on_frame_spinbox_valueChanged(self, i):
        self.img = self.hdul[0].data[self.frame_spinbox.value() - 1, :, :]

        self.update_fli_view()

    @Slot(bool)
    def on_centering_button_clicked(self, checked=None):
        if self.centering:
            self.exit_manual_centering(requested_by_user=True)
        else:
            self.enter_manual_centering(requested_by_user=True)

    def enter_manual_centering(self, requested_by_user=False):
        # If KalAO ICS request centering while user activated centering mode, switch the flag
        if self.centering and not requested_by_user:
            self.centering_requested_by_user = False
            return

        if not self.centering:
            self.centering = True
            self.centering_requested_by_user = requested_by_user

            self.wfs_fov.setVisible(True)

            self.zoom_vertical_line.setVisible(True)
            self.zoom_horizontal_line.setVisible(True)

            self.window_combobox.setCurrentIndex(
                self.window_combobox.findData(FollowMode.MOUSE))
            self.window_combobox.setEnabled(False)

            self.zoom_level = 16

            self.update_zoom_view()

            self.centering_button.setText('Validate Manual Centering')
            self.status_label.setText(
                'Manual centering requested. Don\'t forget to validate.')
            self.status_label.setStyleSheet(f'color: {Color.RED.name()};')

            if not requested_by_user:
                msgbox = KMessageBox(self)
                msgbox.setIcon(QMessageBox.Information)
                msgbox.setText("<b>Manual centering needed!</b>")
                msgbox.setInformativeText(
                    'Manual centering has been requested.\n\nClick on a star to center it.\n\nValidate using the "Validate Manual Centering" button.'
                )
                msgbox.setModal(False)
                msgbox.show()

    def exit_manual_centering(self, requested_by_user=False):
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
            self.status_label.setText('')

            # Send offsets only if centering requested KalAO ICS and validation was by user
            if not self.centering_requested_by_user and requested_by_user:
                self.action_send(self.centering_button,
                                 self.backend.get_centering_validate)

    def hover_xyv_to_str_fli(self, x, y, v):
        if x != -1 and y != -1:
            if self.window_combobox.currentData() == FollowMode.MOUSE:
                self.zoom_center_x = x
                self.zoom_center_y = y

                self.update_zoom_view()

            if self.centering:
                self.vertical_line.setLine(x, 0, x, self.img_height)
                self.horizontal_line.setLine(0, y, self.img_width, y)

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
        if not 0 <= x < self.img_width or not 0 <= y < self.img_height:
            return

        if self.centering:
            self.action_send([], self.backend.set_centering_manual, x=x, y=y)

        if self.window_combobox.currentData() != FollowMode.FIXED:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def fli_dragged(self, x, y, dx, dy):
        if not 0 <= x < self.img_width or not 0 <= y < self.img_height:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def fli_scrolled(self, x, y, z):
        if not 0 <= x < self.img_width or not 0 <= y < self.img_height:
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

        if not 0 <= x < self.img_width or not 0 <= y < self.img_height:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def zoom_scrolled(self, x, y, z):
        hw = self.zoom_half_width
        hh = self.zoom_half_height

        fx = (x - self.zoom_center_x) / hw
        fy = (y - self.zoom_center_y) / hh

        if not 0 <= x < self.img_width or not 0 <= y < self.img_height:
            return

        if z > 0:
            self.zoom_level *= 2

            if self.zoom_level > self.zoom_max:
                self.zoom_level = self.zoom_max

            elif self.window_combobox.currentData() == FollowMode.FIXED:
                self.zoom_center_x = round(x - fx*hw/2)
                self.zoom_center_y = round(y - fy*hh/2)

        else:
            self.zoom_level //= 2

            if self.zoom_level < self.zoom_min:
                self.zoom_level = self.zoom_min

            elif self.window_combobox.currentData() == FollowMode.FIXED:
                self.zoom_center_x = round(x - fx*hw*2)
                self.zoom_center_y = round(y - fy*hh*2)

        self.update_zoom_view()

    def update_image(self, hdul):
        if hdul is None:
            return

        if hdul[0].data is None:
            return
        elif len(hdul[0].data.shape) == 2:
            img = hdul[0].data
            with QSignalBlocker(self.frame_spinbox):
                self.frame_spinbox.setMaximum(1)
                self.frame_spinbox.setValue(1)
        elif len(hdul[0].data.shape) == 3:
            with QSignalBlocker(self.frame_spinbox):
                self.frame_spinbox.setMaximum(hdul[0].data.shape[0])

                if self.frame_spinbox.value() == hdul[0].data.shape[0] - 1:
                    self.frame_spinbox.setValue(hdul[0].data.shape[0])

            img = hdul[0].data[self.frame_spinbox.value() - 1, :, :]
        else:
            raise Exception('Unexpected shape for FLI image')

        if 'DATE' in hdul[0].header:
            self.timestamp = datetime.fromisoformat(
                hdul[0].header['DATE']).replace(tzinfo=timezone.utc)
        else:
            self.timestamp = None

        if 'CRPIX1' in hdul[0].header:
            self.data_center_x = hdul[0].header['CRPIX1']

        if 'CRPIX2' in hdul[0].header:
            self.data_center_y = hdul[0].header['CRPIX2']

        #self.fli_view.setNEIndicator(parang from keywords)
        self.on_onsky_checkbox_stateChanged(self.onsky_checkbox.checkState())

        self.hdul = hdul
        self.img = img

        self.update_fli_view()

    def update_fli_view(self):
        if self.img_width != self.img.shape[
                1] or self.img_height != self.img.shape[0]:
            self.img_width = self.img.shape[1]
            self.img_height = self.img.shape[0]
            self.zoom_center_x = self.img_width // 2
            self.zoom_center_y = self.img_height // 2

            self.zoom_level = self.zoom_min

            self.zoom_max = 2**(
                math.floor(np.log2(min(self.img_width, self.img_height))) - 2)

        self.stars, self.bad_pixels = starfinder.find_stars_and_bad_pixels(
            self.img, num=1)

        if len(self.stars) == 0:
            self.star_x = np.nan
            self.star_y = np.nan
            self.star_peak = np.nan
            self.star_fwhm = np.nan
        else:
            self.star_x = self.stars[0].x
            self.star_y = self.stars[0].y
            self.star_peak = self.stars[0].peak
            self.star_fwhm = self.stars[0].fwhm

        for item in self.stars_itemgroup.childItems():
            self.fli_view.scene.removeItem(item)

        pen = QPen(Color.GREEN, 1.5, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin)
        pen.setCosmetic(True)
        for star in self.stars:
            ellipse_item = self.fli_view.scene.addEllipse(
                star.x - star.fwhm_w / 2, star.y - star.fwhm_h / 2,
                star.fwhm_w, star.fwhm_h, pen)
            ellipse_item.setTransformOriginPoint(QPointF(star.x, star.y))
            ellipse_item.setRotation(star.fwhm_angle)

            self.stars_itemgroup.addToGroup(ellipse_item)
            self.stars_itemgroup.setZValue(1)

        if self.cuts_combobox.currentIndex == 0:
            img_nan = self.img.copy()
            img_nan[self.bad_pixels] = np.nan
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

        self.saturation = self.img.max() / self.image_info['max']

        self.fli_view.setImage(self.img, img_min, img_max,
                               self.scale_combobox.currentData())

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
        hw = self.zoom_half_width = self.img_width // self.zoom_level // 2
        hh = self.zoom_half_height = self.img_height // self.zoom_level // 2

        with QSignalBlocker(self.x_spinbox):
            self.x_spinbox.setValue(x - self.data_center_x)

        with QSignalBlocker(self.y_spinbox):
            self.y_spinbox.setValue(y - self.data_center_y)

        with QSignalBlocker(self.zoom_spinbox):
            self.zoom_spinbox.setValue(self.zoom_level)
            self.update_zoom_spinbox_suffix()

        self.zoom_window.setRect(x - hw, y - hh, 2 * hw, 2 * hh)
        self.zoom_vertical_line.setLine(x, y - hh, x, y + hh)
        self.zoom_horizontal_line.setLine(x - hw, y, x + hw, y)

        zoom = image.cut(self.img, [2 * hw, 2 * hh], [x, y], overflow='cut')

        offset_x = max(x - hw, 0)
        offset_y = max(y - hh, 0)

        self.zoom_view.setImage(zoom, self.min_spinbox.value(),
                                self.max_spinbox.value(),
                                self.scale_combobox.currentData(),
                                view=QRectF(x - hw, y - hh, 2 * hw, 2 * hh),
                                offset=QPointF(offset_x, offset_y))

    def update_labels(self):
        if self.timestamp is None:
            self.timestamp_label.updateText(timestamp='--')
        else:
            self.timestamp_label.updateText(
                timestamp=self.timestamp.strftime('%H:%M:%S %d-%m-%Y'))

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
        size_x = 2 * self.zoom_half_width * self.axis_scaling
        size_y = 2 * self.zoom_half_height * self.axis_scaling
        self.zoom_spinbox.setSuffix(
            f'x ({size_x:.{self.axis_precision}f}{self.axis_unit} x {size_y:.{self.axis_precision}f}{self.axis_unit})'
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

        self.fli_view.setTickParams(5, 5, 5, 10, ticks_x, ticks_y)

    def closeEvent(self, event):
        if self.file is None:
            self.backend.fli_image_updated.disconnect(self.fli_image_updated)
            event.accept()

    def showEvent(self, event):
        if self.file is None:
            self.backend.fli_image_updated.connect(self.fli_image_updated,
                                                   Qt.UniqueConnection)
        event.accept()
