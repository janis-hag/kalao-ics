import math
from datetime import datetime, timezone
from enum import StrEnum

import numpy as np

from astropy.io import fits

from PySide6.QtCore import (QAbstractTableModel, QMargins, QMarginsF, QPointF,
                            QRectF, QSignalBlocker, QSortFilterProxyModel,
                            Slot)
from PySide6.QtGui import QAction, QActionGroup, QPen, Qt
from PySide6.QtWidgets import QHeaderView, QMessageBox

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


class FITSCardsModel(QAbstractTableModel):
    def __init__(self, parent):
        super().__init__(parent)
        self.test_data = []

    def rowCount(self, parent):
        return len(self.test_data)

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole:
            return self.test_data[row][col]

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            match section:
                case 0:
                    return 'Keyword'
                case 1:
                    return 'Value'
                case 2:
                    return 'Comment'

    def update_data(self, header):
        self.layoutAboutToBeChanged.emit()

        self.test_data = []

        for keyword in header.keys():
            if keyword == 'COMMENT':
                continue

            if len(keyword) > config.FITS.max_length_without_HIERARCH:
                true_keyword = f'HIERARCH {keyword}'
            else:
                true_keyword = keyword

            self.test_data.append(
                (true_keyword, header[keyword], header.comments[keyword]))

        self.layoutChanged.emit()


class FITSViewerWindow(KMainWindow, BackendActionMixin, MinMaxMixin,
                       SceneHoverMixin, BackendDataMixin):
    image_info = config.Images.fli

    data_unit = ' ADU'
    data_precision = 0
    data_center_x = 0
    data_center_y = 0

    axis_unit = ' px'
    axis_precision = 0
    axis_scaling = 1

    img_width = np.nan
    img_height = np.nan

    zoom_center_x = 0
    zoom_center_y = 0
    zoom_half_width = np.nan
    zoom_half_height = np.nan
    zoom_level = 16
    zoom_min = 2
    zoom_max = 128

    img = None

    saturation = np.nan
    timestamp = None
    star_x = np.nan
    star_y = np.nan
    star_peak = np.nan
    star_fwhm = np.nan

    ticks_x = []
    ticks_y = []

    centering = False
    centering_requested_by_user = False

    WFS_fov = 4 * config.WFS.plate_scale / config.Camera.plate_scale

    keywords_table_size = 300

    def __init__(self, backend, hdul=None, file=None, on_sky_unit=False,
                 parent=None):
        super().__init__(parent)

        self.backend = backend
        self.hdul = hdul
        self.file = file

        loadUi('fits_viewer.ui', self)

        self.exit_manual_centering_button.setVisible(False)

        self.keywords_widget.setVisible(False)
        self.splitter.handle(1).setEnabled(False)

        self.resize(1400, 600)

        self.init_minmax([self.image_view, self.zoom_view, self.colorbar])

        self.image_view.setView(self.image_info['shape'])

        margins = QMarginsF(10, 10, 40, 30)
        self.zoom_view.setMargins(margins)
        self.image_view.setMargins(margins)

        pen = QPen(Color.PURPLE, 1.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.zoom_window = self.image_view.scene().addRect(-1, -1, 0, 0, pen)
        self.zoom_window.setZValue(1)

        pen = QPen(Color.BLUE, 1.5, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.wfs_fov = self.image_view.scene().addEllipse(
            self.data_center_x - self.WFS_fov / 2, self.data_center_y -
            self.WFS_fov / 2, self.WFS_fov, self.WFS_fov, pen)
        self.wfs_fov.setZValue(1)
        self.wfs_fov.setVisible(False)

        pen = QPen(Color.GREEN, 1.5, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.vertical_line = self.image_view.scene().addLine(-1, -1, 0, 0, pen)
        self.vertical_line.setZValue(1)
        self.vertical_line.setVisible(False)

        self.horizontal_line = self.image_view.scene().addLine(
            -1, -1, 0, 0, pen)
        self.horizontal_line.setZValue(1)
        self.horizontal_line.setVisible(False)

        self.zoom_vertical_line = self.zoom_view.scene().addLine(
            -1, -1, 0, 0, pen)
        self.zoom_vertical_line.setZValue(1)
        self.zoom_vertical_line.setVisible(False)

        self.zoom_horizontal_line = self.zoom_view.scene().addLine(
            -1, -1, 0, 0, pen)
        self.zoom_horizontal_line.setZValue(1)
        self.zoom_horizontal_line.setVisible(False)

        self.stars_itemgroup = self.image_view.scene().createItemGroup([])

        self.colormap_actiongroup = QActionGroup(self.colormap_menu)
        self.colormap_actiongroup.setExclusive(True)
        self.colormap_actiongroup.triggered.connect(
            self.on_colormap_actiongroup_triggered)

        for colormap in colormaps.get_all_colormaps(exclude_transparent=True):
            action = QAction(colormap.__name__)
            action.setCheckable(True)
            action.data = colormap()
            self.colormap_menu.addAction(action)
            self.colormap_actiongroup.addAction(action)

            if colormap.__name__ == 'BlackBody':
                action.trigger()

        self.scale_actiongroup = QActionGroup(self.scale_menu)
        self.scale_actiongroup.setExclusive(True)
        self.scale_actiongroup.triggered.connect(
            self.on_scale_actiongroup_triggered)

        for scale in Scale:
            action = QAction(str(scale.value()))
            action.setCheckable(True)
            action.data = scale.value
            self.scale_menu.addAction(action)
            self.scale_actiongroup.addAction(action)

            if scale == Scale.LOG:
                action.trigger()

        self.cuts_actiongroup = QActionGroup(self.cuts_menu)
        self.cuts_actiongroup.setExclusive(True)
        self.cuts_actiongroup.triggered.connect(
            self.on_cuts_actiongroup_triggered)

        for cuts in Cuts:
            action = QAction(str(cuts.value))
            action.setCheckable(True)
            action.data = cuts.value
            self.cuts_menu.addAction(action)
            self.cuts_actiongroup.addAction(action)

            if cuts == Cuts.MINMAX:
                action.trigger()

        self.zoomwindow_actiongroup = QActionGroup(self.zoomwindow_menu)
        self.zoomwindow_actiongroup.setExclusive(True)
        self.zoomwindow_actiongroup.triggered.connect(
            self.on_zoomwindow_actiongroup_triggered)

        for mode in FollowMode:
            action = QAction(mode.value)
            action.setCheckable(True)
            action.data = mode.value
            self.zoomwindow_menu.addAction(action)
            self.zoomwindow_actiongroup.addAction(action)

            if mode == FollowMode.FIXED:
                action.trigger()

        self.image_view.hovered.connect(self.hover_xyv_to_str_camera)
        self.zoom_view.hovered.connect(self.hover_xyv_to_str_zoom)

        self.image_view.scene().clicked.connect(self.camera_clicked)
        self.image_view.scene().dragged.connect(self.camera_dragged)
        self.image_view.scene().scrolled.connect(self.camera_scrolled)

        self.zoom_view.scene().clicked.connect(self.zoom_clicked)
        self.zoom_view.scene().scrolled.connect(self.zoom_scrolled)

        self.onsky_checkbox.setChecked(on_sky_unit)
        self.on_onsky_checkbox_stateChanged(self.onsky_checkbox.checkState())

        self.hovered.connect(self.info_to_statusbar)

        if self.file is None:
            backend.camera_image_updated.connect(self.camera_image_updated,
                                                 Qt.UniqueConnection)
        else:
            self.setWindowTitle(f'{self.file.name} - {self.windowTitle()}')
            hdul = fits.open(self.file)

            self.centering_menu.setEnabled(False)

        self.model = FITSCardsModel(self)
        self.proxymodel = QSortFilterProxyModel(self)
        self.proxymodel.setSourceModel(self.model)
        self.keywords_table.setModel(self.proxymodel)

        horizontal_header = self.keywords_table.horizontalHeader()
        horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        horizontal_header.setSortIndicatorClearable(True)
        horizontal_header.setSortIndicator(-1, Qt.AscendingOrder)

        if hdul is not None:
            self.update_image(hdul)

        self.show()
        self.center()

    def camera_image_updated(self, data):
        hdul = self.consume_fits_full(data, config.FITS.last_image_all)

        if hdul is not None:
            self.update_image(hdul)

    def on_colormap_actiongroup_triggered(self, action):
        self.image_view.updateColormap(action.data)
        self.zoom_view.updateColormap(action.data)
        self.colorbar.setColormap(action.data)

    def on_scale_actiongroup_triggered(self, action):
        self.image_view.updateScale(action.data)
        self.zoom_view.updateScale(action.data)
        self.colorbar.updateScale(action.data)

    def on_cuts_actiongroup_triggered(self, action):
        self.autoscale_button.setChecked(True)
        self.update_image_view()

    def on_zoomwindow_actiongroup_triggered(self, action):
        if self.zoomwindow_actiongroup.checkedAction().data == FollowMode.STAR:
            self.update_zoom_view()

    @Slot(int)
    def on_frame_spinbox_valueChanged(self, i):
        with QSignalBlocker(self.frame_slider):
            self.frame_slider.setValue(i)

        self.img = self.hdul[0].data[self.frame_spinbox.value() - 1, :, :]

        self.update_image_view()

    @Slot(int)
    def on_frame_slider_valueChanged(self, i):
        with QSignalBlocker(self.frame_spinbox):
            self.frame_spinbox.setValue(i)

        self.img = self.hdul[0].data[self.frame_spinbox.value() - 1, :, :]

        self.update_image_view()

    @Slot(bool)
    def on_enter_manual_centering_action_triggered(self, checked=None):
        self.enter_manual_centering(requested_by_user=True)

    @Slot(bool)
    def on_exit_manual_centering_button_clicked(self, checked=None):
        self.exit_manual_centering(requested_by_user=True)

    def enter_manual_centering(self, requested_by_user=False):
        # If KalAO ICS request centering while user activated centering mode, switch the flag
        if self.centering and not requested_by_user:
            self.centering_requested_by_user = False
            return

        if not self.centering:
            self.enter_manual_centering_action.setEnabled(False)
            self.exit_manual_centering_button.setVisible(True)

            self.wfs_fov.setVisible(True)

            self.zoom_vertical_line.setVisible(True)
            self.zoom_horizontal_line.setVisible(True)

            self.previous_follow_mode = self.zoomwindow_actiongroup.checkedAction(
            )
            for action in self.zoomwindow_actiongroup.actions():
                if action.data == FollowMode.MOUSE:
                    action.trigger()
            self.zoomwindow_actiongroup.setEnabled(False)

            self.previous_zoom_level = self.zoom_level
            self.zoom_level = 16

            self.update_zoom_view()

            if not requested_by_user:
                msgbox = KMessageBox(self)
                msgbox.setIcon(QMessageBox.Information)
                msgbox.setText('<b>Manual centering needed!</b>')
                msgbox.setInformativeText(
                    'Manual centering has been requested.\n\nClick on a star to center it.\n\nValidate using the "Validate Manual Centering" button.'
                )
                msgbox.setModal(False)
                msgbox.show()

            self.centering = True
            self.centering_requested_by_user = requested_by_user

    def exit_manual_centering(self, requested_by_user=False):
        if self.centering:
            self.enter_manual_centering_action.setEnabled(True)
            self.exit_manual_centering_button.setVisible(False)

            self.wfs_fov.setVisible(False)

            self.zoom_vertical_line.setVisible(False)
            self.zoom_horizontal_line.setVisible(False)

            self.zoomwindow_actiongroup.setEnabled(True)
            self.previous_follow_mode.trigger()

            self.zoom_level = self.previous_zoom_level

            self.zoom_center_x = self.data_center_x
            self.zoom_center_y = self.data_center_y

            self.update_zoom_view()

            # Update centering flag only if centering requested KalAO ICS and validation was by user
            if not self.centering_requested_by_user and requested_by_user:
                self.action_send(self.centering_button,
                                 self.backend.centering_validate)

            self.centering = False

    def hover_xyv_to_str_camera(self, x, y, v):
        if not np.isnan(x) and not np.isnan(y):
            x = int(x)
            y = int(y)

            if self.zoomwindow_actiongroup.checkedAction(
            ).data == FollowMode.MOUSE:
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
            if self.zoomwindow_actiongroup.checkedAction(
            ).data == FollowMode.MOUSE:
                self.zoom_center_x = self.data_center_x
                self.zoom_center_y = self.data_center_y

                self.update_zoom_view()

            if self.centering:
                self.vertical_line.setVisible(False)
                self.horizontal_line.setVisible(False)

            self.hovered.emit('')

    def hover_xyv_to_str_zoom(self, x, y, v):
        if not np.isnan(x) and not np.isnan(y):
            x = int(x)
            y = int(y)

            string = f'X: {(x-self.data_center_x)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, Y: {(y-self.data_center_y)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, V: {v*self.data_scaling:.{self.data_precision}f}{self.data_unit}'

            self.hovered.emit(string)
        else:
            self.hovered.emit('')

    def camera_clicked(self, x, y):
        if not 0 <= x < self.img_width or not 0 <= y < self.img_height:
            return

        if self.centering:
            self.action_send([], self.backend.centering_manual,
                             dx=self.data_center_x - x,
                             dy=self.data_center_y - y)

        if self.zoomwindow_actiongroup.checkedAction(
        ).data != FollowMode.FIXED:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def camera_dragged(self, x, y, dx, dy):
        if not 0 <= x < self.img_width or not 0 <= y < self.img_height:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def camera_scrolled(self, x, y, z):
        if not 0 <= x < self.img_width or not 0 <= y < self.img_height:
            return

        if self.zoomwindow_actiongroup.checkedAction(
        ).data == FollowMode.FIXED:
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
        if self.zoomwindow_actiongroup.checkedAction(
        ).data != FollowMode.FIXED:
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

            elif self.zoomwindow_actiongroup.checkedAction(
            ).data == FollowMode.FIXED:
                self.zoom_center_x = round(x - fx*hw/2)
                self.zoom_center_y = round(y - fy*hh/2)

        else:
            self.zoom_level //= 2

            if self.zoom_level < self.zoom_min:
                self.zoom_level = self.zoom_min

            elif self.zoomwindow_actiongroup.checkedAction(
            ).data == FollowMode.FIXED:
                self.zoom_center_x = round(x - fx*hw*2)
                self.zoom_center_y = round(y - fy*hh*2)

        self.update_zoom_view()

    def update_image(self, hdul):
        if hdul is None:
            return

        self.update_keywords_table(hdul[0].header)

        if hdul[0].data is None:
            return

        elif len(hdul[0].data.shape) == 2:
            self.frame_label.setEnabled(False)

            with QSignalBlocker(self.frame_spinbox):
                self.frame_spinbox.setMaximum(1)
                self.frame_spinbox.setValue(1)
                self.frame_spinbox.setEnabled(False)

            with QSignalBlocker(self.frame_slider):
                self.frame_slider.setMaximum(1)
                self.frame_slider.setValue(1)
                self.frame_slider.setEnabled(False)

            self.img = hdul[0].data

        elif len(hdul[0].data.shape) == 3:
            on_last = self.frame_spinbox.value() == self.frame_spinbox.maximum(
            )

            self.frame_label.setEnabled(True)

            with QSignalBlocker(self.frame_spinbox):
                self.frame_spinbox.setMaximum(hdul[0].data.shape[0])
                self.frame_slider.setEnabled(True)

                if on_last:
                    self.frame_spinbox.setValue(hdul[0].data.shape[0])

            with QSignalBlocker(self.frame_slider):
                self.frame_slider.setMaximum(hdul[0].data.shape[0])
                self.frame_slider.setEnabled(True)

                if on_last:
                    self.frame_slider.setValue(hdul[0].data.shape[0])

            self.img = hdul[0].data[self.frame_spinbox.value() - 1, :, :]

        else:
            raise Exception('Unexpected shape for camera image')

        self.hdul = hdul
        hdu = hdul[0]

        if 'DATE' in hdu.header:
            self.timestamp = datetime.fromisoformat(
                hdu.header['DATE']).replace(tzinfo=timezone.utc).astimezone()
        else:
            self.timestamp = None

        self.data_unit = ' ' + hdu.header.get('BUNIT', 'ADU')
        self.data_center_x = hdu.header.get(
            'CRPIX1', 1) - 1  # Note: FITS indexing starts at 1
        self.data_center_y = hdu.header.get(
            'CRPIX2', 1) - 1  # Note: FITS indexing starts at 1
        self.axis_unit_x = hdu.header.get('CUNIT1', '"')
        self.axis_unit_y = hdu.header.get('CUNIT2', '"')
        cd11 = hdu.header.get('CD1_1', 0)
        cd12 = hdu.header.get('CD1_2', 0)
        cd21 = hdu.header.get('CD2_1', 0)
        cd22 = hdu.header.get('CD2_2', 0)

        cdelt1 = np.sqrt(cd11**2 + cd21**2)
        cdelt2 = np.sqrt(cd12**2 + cd22**2)

        if np.sign(cd11*cd22 - cd12*cd21) == -1:
            cdelt1 = -cdelt1

        crota2 = np.arctan2(
            np.sign(cdelt1 * cdelt2) * cd12,
            cd22)  # = np.arctan2(-np.sign(cdelt1*cdelt2)*cd21, cd11)
        crota2 *= 180 / np.pi

        self.wfs_fov.setRect(self.data_center_x - self.WFS_fov / 2,
                             self.data_center_y - self.WFS_fov / 2,
                             self.WFS_fov, self.WFS_fov)

        #self.image_view.setNEIndicator(parang from keywords)

        # Zoom window (reset if image size changed)

        if self.img_width != self.img.shape[
                1] or self.img_height != self.img.shape[0]:
            self.img_width = self.img.shape[1]
            self.img_height = self.img.shape[0]
            self.zoom_center_x = self.img_width // 2
            self.zoom_center_y = self.img_height // 2

            self.zoom_level = self.zoom_min

            self.zoom_max = 2**(
                math.floor(np.log2(min(self.img_width, self.img_height))) - 2)

        # Find stars

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
            self.image_view.scene().removeItem(item)

        pen = QPen(Color.GREEN, 1.5, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin)
        pen.setCosmetic(True)
        for star in self.stars:
            ellipse_item = self.image_view.scene().addEllipse(
                star.x - star.fwhm_w / 2, star.y - star.fwhm_h / 2,
                star.fwhm_w, star.fwhm_h, pen)
            ellipse_item.setTransformOriginPoint(QPointF(star.x, star.y))
            ellipse_item.setRotation(star.fwhm_angle)

            self.stars_itemgroup.addToGroup(ellipse_item)
            self.stars_itemgroup.setZValue(1)

        # Ticks

        x_tick_start = -self.data_center_x
        x_tick_stop = -self.data_center_x + self.img_width
        self.ticks_x = np.linspace(x_tick_start, x_tick_stop, 9)

        y_tick_start = -self.data_center_y
        y_tick_stop = -self.data_center_y + self.img_width
        self.ticks_y = np.linspace(y_tick_start, y_tick_stop, 9)

        self.update_image_view()
        self.update_labels()
        self.update_ticks()

    def update_image_view(self):
        if self.img is None:
            return

        img_min, img_max = self.compute_min_max(
            self.img,
            self.cuts_actiongroup.checkedAction().data)

        self.saturation = self.img.max() / self.image_info['max']

        self.image_view.setImage(self.img, img_min, img_max,
                                 self.scale_actiongroup.checkedAction().data)

        self.colorbar.setTrueMinMax(self.img.min(), self.img.max())
        self.colorbar.updateMinMax(img_min, img_max)

        self.update_zoom_view()

    def update_zoom_view(self):
        if self.zoomwindow_actiongroup.checkedAction(
        ).data == FollowMode.STAR and not np.isnan([self.star_x, self.star_y
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

        x = round(x)
        y = round(y)

        self.zoom_window.setRect(x - hw, y - hh, 2 * hw, 2 * hh)
        self.zoom_vertical_line.setLine(x, y - hh, x, y + hh)
        self.zoom_horizontal_line.setLine(x - hw, y, x + hw, y)

        zoom = image.cut(self.img, (2 * hw, 2 * hh), (x, y), overflow='cut')

        offset_x = max(x - hw, 0)
        offset_y = max(y - hh, 0)

        self.zoom_view.setImage(zoom, self.min_spinbox.value(),
                                self.max_spinbox.value(),
                                self.scale_actiongroup.checkedAction().data,
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

    def update_ticks(self):
        ticks_x = []
        ticks_y = []

        for x in self.ticks_x:
            tick_label = f'{x*self.axis_scaling:.{self.axis_precision}f}'
            tick_pos = x + self.data_center_x
            ticks_x.append((tick_pos, tick_label))

        for y in self.ticks_y:
            tick_label = f'{y*self.axis_scaling:.{self.axis_precision}f}'
            tick_pos = y + self.data_center_y
            ticks_y.append((tick_pos, tick_label))

        self.image_view.setTickParams(0, 5, 5, 10, ticks_x, ticks_y)

    def update_zoom_spinbox_suffix(self):
        size_x = 2 * self.zoom_half_width * self.axis_scaling
        size_y = 2 * self.zoom_half_height * self.axis_scaling
        self.zoom_spinbox.setSuffix(
            f'x ({size_x:.{self.axis_precision}f}{self.axis_unit} x {size_y:.{self.axis_precision}f}{self.axis_unit})'
        )

    @Slot(int)
    def on_onsky_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.axis_unit = '"'
            self.axis_precision = 1
            self.axis_scaling = config.Camera.plate_scale
        else:
            self.axis_unit = ' px'
            self.axis_precision = 0
            self.axis_scaling = 1

        self.update_labels()
        self.update_zoom_spinbox_suffix()

        self.x_spinbox.setScale(self.axis_scaling, self.axis_precision)
        self.y_spinbox.setScale(self.axis_scaling, self.axis_precision)
        self.x_spinbox.setSuffix(self.axis_unit)
        self.y_spinbox.setSuffix(self.axis_unit)

        self.update_ticks()

    def update_keywords_table(self, header):
        self.model.update_data(header)

    @Slot(bool)
    def on_keywords_toolbutton_clicked(self, checked):
        if checked:
            sizes = self.splitter.sizes()

            self.keywords_toolbutton.setArrowType(Qt.DownArrow)
            self.keywords_widget.setVisible(True)
            self.resize(self.size().grownBy(
                QMargins(0, 0, 0, self.keywords_table_size)))

            self.splitter.setSizes([
                sizes[0], sizes[1] + self.keywords_table_size
            ])

            self.splitter.handle(1).setEnabled(True)
        else:
            sizes = self.splitter.sizes()
            self.keywords_table_size = sizes[
                1] - self.keywords_button_widget.height()

            self.keywords_toolbutton.setArrowType(Qt.RightArrow)
            self.keywords_widget.setVisible(False)

            self.resize(self.size().grownBy(
                QMargins(0, 0, 0, -self.keywords_table_size)))
            self.splitter.setSizes([
                sizes[0], self.keywords_button_widget.height()
            ])

            self.splitter.handle(1).setEnabled(False)

    @Slot(str)
    def on_keywords_filter_lineedit_textEdited(self, text):
        if text == '':
            self.proxymodel.setFilterRegularExpression('')
        else:
            self.proxymodel.setFilterKeyColumn(-1)
            self.proxymodel.setFilterCaseSensitivity(Qt.CaseInsensitive)
            self.proxymodel.setFilterFixedString(text)

    def closeEvent(self, event):
        if self.file is None:
            self.backend.camera_image_updated.disconnect(
                self.camera_image_updated)
            event.accept()

    def showEvent(self, event):
        if self.file is None:
            self.backend.camera_image_updated.connect(
                self.camera_image_updated, Qt.UniqueConnection)
        event.accept()
