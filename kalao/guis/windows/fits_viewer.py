import math
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

import numpy as np

from astropy.io import fits

from PySide6.QtCore import (QAbstractTableModel, QMargins, QMarginsF,
                            QModelIndex, QObject, QPointF, QRectF,
                            QSignalBlocker, QSortFilterProxyModel, QTimer,
                            QUrl, Signal, Slot)
from PySide6.QtGui import (QAction, QActionGroup, QCloseEvent, QIcon, QPen,
                           QShowEvent, Qt)
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
from PySide6.QtWidgets import (QHeaderView, QLineEdit, QMessageBox,
                               QSizePolicy, QWidget)

from compiled.ui_fits_viewer import Ui_FITSViewerWindow

from kalao.common import image, kstring, starfinder

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils import colormaps
from kalao.guis.utils.definitions import Color, Cuts, Scale
from kalao.guis.utils.mixins import BackendActionMixin, BackendDataMixin
from kalao.guis.utils.widgets import KMainWindow, KMessageBox

import config


class FollowMode(StrEnum):
    FIXED = 'Fixed'
    MOUSE = 'Follow mouse'
    STAR = 'Follow star'


class FITSCardsModel(QAbstractTableModel):
    _columns = [
        'Keyword',
        'Value',
        'Comment',
    ]

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self._data = []

    def rowCount(self, parent: QModelIndex) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role: int) -> Any:
        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole:
            return self._data[row][col]

        return None

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int) -> str:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._columns[section]

    def update_data(self, header: fits.Header) -> None:
        self.layoutAboutToBeChanged.emit()

        self._data = []

        for keyword in header.keys():
            if keyword == 'COMMENT':
                continue

            if len(keyword) > config.FITS.max_length_without_HIERARCH:
                true_keyword = f'HIERARCH {keyword}'
            else:
                true_keyword = keyword

            self._data.append(
                (true_keyword, header[keyword], header.comments[keyword]))

        self.layoutChanged.emit()


class FITSViewerWindow(KMainWindow, BackendActionMixin, BackendDataMixin):
    image_info = config.Images.fli

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

    keywords_table_size = 300  # px

    hovered = Signal(str)

    def __init__(self, backend: AbstractBackend, hdul: fits.HDUList = None,
                 file: Path = None, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend
        self.hdul = hdul
        self.file = file

        self.ui = Ui_FITSViewerWindow()
        self.ui.setupUi(self)

        # Manual centering notification

        self.media_devices = QMediaDevices()
        self.media_devices.audioOutputsChanged.connect(
            self.on_audiooutputs_changed)
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setDevice(self.media_devices.defaultAudioOutput())
        self.audio_output.setVolume(1.0)
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(
            QUrl('qrc:/assets/sounds/alarm-clock-elapsed.oga'))

        self.centering_timer = QTimer(self)
        self.centering_timer.setInterval(
            int(config.GUI.manual_centering_alarm_interval * 1000))
        self.centering_timer.timeout.connect(self.centering_notification)

        self.ui.centering_widget.setSizePolicy(QSizePolicy.Policy.Preferred,
                                               QSizePolicy.Policy.Ignored)

        self.ui.centering_volume_button.setChecked(True)

        # Keywords

        self.ui.keywords_widget.setVisible(False)
        self.ui.keywords_splitter.handle(1).setEnabled(False)

        self.keywords_model = FITSCardsModel(self)
        self.keywords_proxymodel = QSortFilterProxyModel(self)
        self.keywords_proxymodel.setSourceModel(self.keywords_model)
        self.ui.keywords_table.setModel(self.keywords_proxymodel)

        horizontal_header = self.ui.keywords_table.horizontalHeader()
        horizontal_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)

        horizontal_header.setSortIndicatorClearable(True)
        horizontal_header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)

        for column_name in self.keywords_model._columns:
            with QSignalBlocker(self.ui.keywords_columns_combobox):
                self.ui.keywords_columns_combobox.addItem(column_name)

        # Base

        self.resize(1400, 600)

        self.ui.minmax_widget.setup([
            self.ui.image_view, self.ui.zoom_view, self.ui.colorbar
        ], ' ADU', 0, 1, -999999, 999999, self.image_info['min'],
                                    self.image_info['max'])
        self.ui.image_view.set_data_md(' ADU', 0)
        self.ui.image_view.set_axis_md(' px', 0)

        self.ui.zoom_view.set_data_md(' ADU', 0)
        self.ui.zoom_view.set_axis_md(' px', 0)

        self.ui.image_view.setView(self.image_info['shape'])

        margins = QMarginsF(10, 10, 40, 30)
        self.ui.zoom_view.setMargins(margins)
        self.ui.image_view.setMargins(margins)

        # Zoom indicator

        pen = QPen(Color.PURPLE, 1.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        self.zoom_window = self.ui.image_view.scene().addRect(
            -1, -1, 0, 0, pen)
        self.zoom_window.setZValue(1)

        # WFS Field of view

        pen = QPen(Color.BLUE, 1.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        self.wfs_fov = self.ui.image_view.scene().addEllipse(
            self.ui.image_view.axis_x_offset - self.WFS_fov / 2,
            self.ui.image_view.axis_y_offset - self.WFS_fov / 2, self.WFS_fov,
            self.WFS_fov, pen)
        self.wfs_fov.setZValue(1)
        self.wfs_fov.setVisible(False)

        # Manual centering crosses

        pen = QPen(Color.GREEN, 1.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        self.vertical_line = self.ui.image_view.scene().addLine(
            -1, -1, 0, 0, pen)
        self.vertical_line.setZValue(1)
        self.vertical_line.setVisible(False)

        self.horizontal_line = self.ui.image_view.scene().addLine(
            -1, -1, 0, 0, pen)
        self.horizontal_line.setZValue(1)
        self.horizontal_line.setVisible(False)

        self.zoom_vertical_line = self.ui.zoom_view.scene().addLine(
            -1, -1, 0, 0, pen)
        self.zoom_vertical_line.setZValue(1)
        self.zoom_vertical_line.setVisible(False)

        self.zoom_horizontal_line = self.ui.zoom_view.scene().addLine(
            -1, -1, 0, 0, pen)
        self.zoom_horizontal_line.setZValue(1)
        self.zoom_horizontal_line.setVisible(False)

        # Stars detection

        self.stars_itemgroup = self.ui.image_view.scene().createItemGroup([])

        # Colormap menu

        self.colormap_actiongroup = QActionGroup(self.ui.colormap_menu)
        self.colormap_actiongroup.setExclusive(True)
        self.colormap_actiongroup.triggered.connect(
            self.on_colormap_actiongroup_triggered)

        for colormap in colormaps.get_all_colormaps(exclude_transparent=True):
            action = QAction(colormap.__name__)
            action.setCheckable(True)
            action.data = colormap()
            self.ui.colormap_menu.addAction(action)
            self.colormap_actiongroup.addAction(action)

            if colormap.__name__ == 'BlackBody':
                action.trigger()

        # Scale menu

        self.scale_actiongroup = QActionGroup(self.ui.scale_menu)
        self.scale_actiongroup.setExclusive(True)
        self.scale_actiongroup.triggered.connect(
            self.on_scale_actiongroup_triggered)

        for scale in Scale:
            action = QAction(str(scale.value()))
            action.setCheckable(True)
            action.data = scale.value
            self.ui.scale_menu.addAction(action)
            self.scale_actiongroup.addAction(action)

            if scale == Scale.LOG:
                action.trigger()

        # Cuts menu

        self.cuts_actiongroup = QActionGroup(self.ui.cuts_menu)
        self.cuts_actiongroup.setExclusive(True)
        self.cuts_actiongroup.triggered.connect(
            self.on_cuts_actiongroup_triggered)

        for cuts in Cuts:
            action = QAction(str(cuts.value))
            action.setCheckable(True)
            action.data = cuts.value
            self.ui.cuts_menu.addAction(action)
            self.cuts_actiongroup.addAction(action)

            if cuts == Cuts.MINMAX:
                action.trigger()

        # Zoom window menu

        self.zoomwindow_actiongroup = QActionGroup(self.ui.zoomwindow_menu)
        self.zoomwindow_actiongroup.setExclusive(True)
        self.zoomwindow_actiongroup.triggered.connect(
            self.on_zoomwindow_actiongroup_triggered)

        for mode in FollowMode:
            action = QAction(mode.value)
            action.setCheckable(True)
            action.data = mode.value
            self.ui.zoomwindow_menu.addAction(action)
            self.zoomwindow_actiongroup.addAction(action)

            if mode == FollowMode.FIXED:
                action.trigger()

        # Connect signals

        self.ui.image_view.hovered.connect(self.hover_xyv_to_str_camera)
        self.ui.zoom_view.hovered.connect(self.hover_xyv_to_str_zoom)

        self.ui.image_view.scene().clicked.connect(self.camera_clicked)
        self.ui.image_view.scene().dragged.connect(self.camera_dragged)
        self.ui.image_view.scene().scrolled.connect(self.camera_scrolled)

        self.ui.zoom_view.scene().clicked.connect(self.zoom_clicked)
        self.ui.zoom_view.scene().scrolled.connect(self.zoom_scrolled)

        self.hovered.connect(self.info_to_statusbar)

        # Open file vs live view

        if self.file is None:
            backend.camera_image_updated.connect(
                self.camera_image_updated, Qt.ConnectionType.UniqueConnection)
        else:
            self.setWindowTitle(f'{self.file.name} - {self.windowTitle()}')
            hdul = fits.open(self.file)

            self.ui.centering_menu.setEnabled(False)

        if hdul is not None:
            self.update_image(hdul)

        self.show()
        self.center()

    def all_updated(self, data: dict[str, Any]) -> None:
        # Note: signal connected only during centering

        centering_timeout = self.consume_dict(data, 'centering_manual',
                                              'timeout', force=True)
        if centering_timeout is not None:
            time_left = centering_timeout - self.consume_metadata(
                data, 'timestamp')
            if time_left < 0:
                time_left = 0
            self.ui.centering_timeout_label.updateText(timeout=time_left)

    def camera_image_updated(self, data: dict[str, Any]) -> None:
        hdul = self.consume_fits_full(data, config.FITS.last_image_all)

        if hdul is not None:
            self.update_image(hdul)

    def on_colormap_actiongroup_triggered(self, action: QAction) -> None:
        self.ui.image_view.updateColormap(action.data)
        self.ui.zoom_view.updateColormap(action.data)
        self.ui.colorbar.setColormap(action.data)

    def on_scale_actiongroup_triggered(self, action: QAction) -> None:
        self.ui.image_view.updateScale(action.data)
        self.ui.zoom_view.updateScale(action.data)
        self.ui.colorbar.updateScale(action.data)

    def on_cuts_actiongroup_triggered(self, action: QAction) -> None:
        self.ui.minmax_widget.ui.autoscale_button.setChecked(True)
        self.update_image_view()

    def on_zoomwindow_actiongroup_triggered(self, action: QAction) -> None:
        if self.zoomwindow_actiongroup.checkedAction().data == FollowMode.STAR:
            self.update_zoom_view()

    @Slot(int)
    def on_frame_spinbox_valueChanged(self, i: int) -> None:
        with QSignalBlocker(self.ui.frame_slider):
            self.ui.frame_slider.setValue(i)

        self.img = self.hdul[0].data[self.ui.frame_spinbox.value() - 1, :, :]

        self.update_image_view()

    @Slot(int)
    def on_frame_slider_valueChanged(self, value: int) -> None:
        with QSignalBlocker(self.ui.frame_spinbox):
            self.ui.frame_spinbox.setValue(value)

        self.img = self.hdul[0].data[self.ui.frame_spinbox.value() - 1, :, :]

        self.update_image_view()

    def on_audiooutputs_changed(self) -> None:
        self.audio_output.setDevice(self.media_devices.defaultAudioOutput())

    @Slot(bool)
    def on_enter_manual_centering_action_triggered(self,
                                                   checked: bool) -> None:
        self.enter_manual_centering(requested_by_user=True)

    @Slot(bool)
    def on_centering_validate_button_clicked(self, checked: bool) -> None:
        self.exit_manual_centering(requested_by_user=True)

    @Slot(bool)
    def on_centering_abort_button_clicked(self, checked: bool) -> None:
        self.action_send([
            self.ui.centering_validate_button, self.ui.centering_abort_button
        ], self.backend.sequencer_abort)

    @Slot(bool)
    def on_centering_spiral_search_button_clicked(self, checked: bool) -> None:
        self.action_send(self.ui.centering_spiral_search_button,
                         self.backend.centering_spiral)

    @Slot(bool)
    def on_centering_star_button_clicked(self, checked: bool) -> None:
        self.action_send(self.ui.centering_star_button,
                         self.backend.centering_star)

    @Slot(bool)
    def on_centering_volume_button_toggled(self, checked: bool) -> None:
        if checked:
            self.ui.centering_volume_button.setIcon(
                QIcon(':/assets/icons/audio-volume-muted.svg'))
            self.centering_timer.stop()
        else:
            self.ui.centering_volume_button.setIcon(
                QIcon(':/assets/icons/audio-volume-high.svg'))
            QTimer.singleShot(0, self.centering_notification)
            self.centering_timer.start()

    def centering_notification(self) -> None:
        self.player.play()

    def enter_manual_centering(self, requested_by_user: bool = False,
                               reason='Unknown') -> None:
        # If KalAO ICS request centering while user activated centering mode, switch the flag
        if self.centering and not requested_by_user:
            self.centering_requested_by_user = False

            self.ui.centering_reason_label.updateText(reason=reason)

            self.backend.all_updated.connect(
                self.all_updated, Qt.ConnectionType.UniqueConnection)
            return

        if not self.centering:
            self.ui.enter_manual_centering_action.setEnabled(False)
            self.ui.centering_widget.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

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
                self.ui.centering_reason_label.updateText(reason=reason)

                msgbox = KMessageBox(self)
                msgbox.setIcon(QMessageBox.Icon.Information)
                msgbox.setText('<b>Manual centering needed!</b>')
                msgbox.setInformativeText(
                    f'Manual centering has been requested.\n\nReason: "{reason}".\n\nClick on a star to center it.\n\nValidate using the "Validate Manual Centering" button.'
                )
                msgbox.setModal(False)
                msgbox.show()

                self.ui.centering_volume_button.setChecked(False)

                self.ui.centering_timeout_label.updateText(timeout=np.nan)
                self.backend.all_updated.connect(
                    self.all_updated, Qt.ConnectionType.UniqueConnection)
            else:
                self.ui.centering_reason_label.updateText(
                    reason='Request by user')
                self.ui.centering_timeout_label.updateText(timeout=np.nan)

            self.centering = True
            self.centering_requested_by_user = requested_by_user

    def exit_manual_centering(self, requested_by_user: bool = False) -> None:
        if self.centering:
            self.ui.enter_manual_centering_action.setEnabled(True)
            self.ui.centering_widget.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Ignored)

            self.wfs_fov.setVisible(False)

            self.zoom_vertical_line.setVisible(False)
            self.zoom_horizontal_line.setVisible(False)

            self.zoomwindow_actiongroup.setEnabled(True)
            self.previous_follow_mode.trigger()

            self.zoom_level = self.previous_zoom_level

            self.zoom_center_x = self.ui.image_view.axis_x_offset
            self.zoom_center_y = self.ui.image_view.axis_y_offset

            self.update_zoom_view()

            # Update centering flag only if centering requested KalAO ICS and validation was by user
            if not self.centering_requested_by_user and requested_by_user:
                self.action_send([
                    self.ui.centering_validate_button,
                    self.ui.centering_abort_button
                ], self.backend.centering_manual_validate)

            self.ui.centering_volume_button.setChecked(True)

            try:
                self.backend.all_updated.disconnect(self.all_updated)
            except RuntimeError:
                pass

            self.centering = False

    def hover_xyv_to_str_camera(self, x: float, y: float, v: float) -> None:
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

            self.update_coords(x, y)
            self.ui.value_spinbox.setValue(v)
        else:
            if self.zoomwindow_actiongroup.checkedAction(
            ).data == FollowMode.MOUSE:
                self.zoom_center_x = self.ui.image_view.axis_x_offset
                self.zoom_center_y = self.ui.image_view.axis_y_offset

                self.update_zoom_view()

            if self.centering:
                self.vertical_line.setVisible(False)
                self.horizontal_line.setVisible(False)

            self.update_coords(np.nan, np.nan)
            self.ui.value_spinbox.setValue(np.nan)

    def hover_xyv_to_str_zoom(self, x: float, y: float, v: float) -> None:
        if not np.isnan(x) and not np.isnan(y):
            x = int(x)
            y = int(y)

            self.update_coords(x, y)
            self.ui.value_spinbox.setValue(v)
        else:
            self.update_coords(np.nan, np.nan)
            self.ui.value_spinbox.setValue(np.nan)

    def camera_clicked(self, x: float, y: float) -> None:
        if not 0 <= x < self.img_width or not 0 <= y < self.img_height:
            return

        if self.centering:
            self.action_send([], self.backend.centering_manual_offsets,
                             dx=self.ui.image_view.axis_x_offset - x,
                             dy=self.ui.image_view.axis_y_offset - y)

        if self.zoomwindow_actiongroup.checkedAction(
        ).data != FollowMode.FIXED:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def camera_dragged(self, x: float, y: float, dx: float, dy: float) -> None:
        if not 0 <= x < self.img_width or not 0 <= y < self.img_height:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def camera_scrolled(self, x: float, y: float, z: float) -> None:
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

    def zoom_clicked(self, x: float, y: float) -> None:
        if self.zoomwindow_actiongroup.checkedAction(
        ).data != FollowMode.FIXED:
            return

        if not 0 <= x < self.img_width or not 0 <= y < self.img_height:
            return

        self.zoom_center_x = round(x)
        self.zoom_center_y = round(y)

        self.update_zoom_view()

    def zoom_scrolled(self, x: float, y: float, z: float) -> None:
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

    def update_image(self, hdul: fits.HDUList) -> None:
        if hdul is None:
            return

        self.update_keywords_table(hdul[0].header)

        if hdul[0].data is None:
            return

        elif len(hdul[0].data.shape) == 2:
            self.ui.frame_label.setEnabled(False)

            with QSignalBlocker(self.ui.frame_spinbox):
                self.ui.frame_spinbox.setMaximum(1)
                self.ui.frame_spinbox.setValue(1)
                self.ui.frame_spinbox.setEnabled(False)

            with QSignalBlocker(self.ui.frame_slider):
                self.ui.frame_slider.setMaximum(1)
                self.ui.frame_slider.setValue(1)
                self.ui.frame_slider.setEnabled(False)

            self.img = hdul[0].data

        elif len(hdul[0].data.shape) == 3:
            on_last = self.ui.frame_spinbox.value(
            ) == self.ui.frame_spinbox.maximum()

            self.ui.frame_label.setEnabled(True)

            with QSignalBlocker(self.ui.frame_spinbox):
                self.ui.frame_spinbox.setMaximum(hdul[0].data.shape[0])
                self.ui.frame_spinbox.setEnabled(True)

                if on_last:
                    self.ui.frame_spinbox.setValue(hdul[0].data.shape[0])

            with QSignalBlocker(self.ui.frame_slider):
                self.ui.frame_slider.setMaximum(hdul[0].data.shape[0])
                self.ui.frame_slider.setEnabled(True)

                if on_last:
                    self.ui.frame_slider.setValue(hdul[0].data.shape[0])

            self.img = hdul[0].data[self.ui.frame_spinbox.value() - 1, :, :]

        else:
            raise Exception('Unexpected shape for camera image')

        self.hdul = hdul
        hdu = hdul[0]

        if 'DATE' in hdu.header:
            self.timestamp = datetime.fromisoformat(
                hdu.header['DATE']).replace(tzinfo=timezone.utc).astimezone()
        else:
            self.timestamp = None

        self.wcs_bunit = ' ' + hdu.header.get('BUNIT', 'ADU')

        self.wcs_crpix1 = hdu.header.get(
            'CRPIX1', 1) - 1  # Note: FITS indexing starts at 1
        self.wcs_crpix2 = hdu.header.get(
            'CRPIX2', 1) - 1  # Note: FITS indexing starts at 1

        self.wcs_crval1 = hdu.header.get('CRVAL1', 0)
        self.wcs_crval2 = hdu.header.get('CRVAL2', 0)

        self.wcs_ctype1 = hdu.header.get('CTYPE1', 'UNK')
        self.wcs_ctype2 = hdu.header.get('CTYPE2', 'UNK')

        self.wcs_cunit1 = hdu.header.get('CUNIT1', '')
        self.wcs_cunit2 = hdu.header.get('CUNIT2', '')

        self.wcs_cd11 = hdu.header.get('CD1_1', 0)
        self.wcs_cd12 = hdu.header.get('CD1_2', 0)
        self.wcs_cd21 = hdu.header.get('CD2_1', 0)
        self.wcs_cd22 = hdu.header.get('CD2_2', 0)

        self.wcs_pc11 = hdu.header.get('PC1_1', 1)
        self.wcs_pc12 = hdu.header.get('PC1_2', 0)
        self.wcs_pc21 = hdu.header.get('PC2_1', 0)
        self.wcs_pc22 = hdu.header.get('PC2_2', 1)

        self.wcs_cdelt1 = hdu.header.get('CDELT1', 1)
        self.wcs_cdelt2 = hdu.header.get('CDELT2', 1)

        self.wcs_radesys = hdu.header.get('RADESYS', None)
        self.wcs_equinox = hdu.header.get('EQUINOX', None)

        if self.wcs_radesys is None:
            if self.wcs_equinox is None:
                self.wcs_radesys = 'ICRS'
            elif self.wcs_equinox < 1984.0:
                self.wcs_radesys = 'FK4'
            elif self.wcs_equinox >= 1984.0:
                self.wcs_radesys = 'FK5'
            else:
                self.wcs_radesys = 'ERROR'

        if self.wcs_equinox is None:
            if self.wcs_radesys == 'ICRS':
                self.wcs_equinox = np.nan
            elif self.wcs_radesys == 'FK4':
                self.wcs_equinox = 1950.0
            elif self.wcs_radesys == 'FK5':
                self.wcs_equinox = 2000.0
            else:
                self.wcs_equinox = np.nan

        if self.wcs_radesys == 'ICRS':
            wcs_equinox_str = ''
        elif self.wcs_radesys == 'FK4':
            wcs_equinox_str = f' (B{self.wcs_equinox})'
        elif self.wcs_radesys == 'FK5':
            wcs_equinox_str = f' (J{self.wcs_equinox})'
        else:
            wcs_equinox_str = f' ({self.wcs_equinox})'

        # cdelt1 = np.sqrt(cd11**2 + cd21**2)
        # cdelt2 = np.sqrt(cd12**2 + cd22**2)
        #
        # if np.sign(cd11*cd22 - cd12*cd21) == -1:
        #     cdelt1 = -cdelt1
        #
        # crota2 = np.arctan2(
        #     np.sign(cdelt1 * cdelt2) * cd12,
        #     cd22)  # = np.arctan2(-np.sign(cdelt1*cdelt2)*cd21, cd11)
        # crota2 *= 180 / np.pi

        self.wfs_fov.setRect(self.wcs_crpix1 - self.WFS_fov / 2,
                             self.wcs_crpix2 - self.WFS_fov / 2, self.WFS_fov,
                             self.WFS_fov)

        self.ui.image_view.setNEIndicator(0)

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
            self.ui.image_view.scene().removeItem(item)

        pen = QPen(Color.GREEN, 1.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)
        for star in self.stars:
            ellipse_item = self.ui.image_view.scene().addEllipse(
                star.x - star.fwhm_w / 2, star.y - star.fwhm_h / 2,
                star.fwhm_w, star.fwhm_h, pen)
            ellipse_item.setTransformOriginPoint(QPointF(star.x, star.y))
            ellipse_item.setRotation(star.fwhm_angle)

            self.stars_itemgroup.addToGroup(ellipse_item)
            self.stars_itemgroup.setZValue(1)

        # Ticks

        ticks_x = np.linspace(0, self.img_width, 9)
        ticks_y = np.linspace(0, self.img_height, 9)
        self.ui.image_view.setTickParams(0, 5, 5, 10, ticks_x, ticks_y)

        # Update

        self.ui.value_spinbox.setSuffix(f' {self.wcs_bunit}')

        self.ui.wcs_system_lineedit.setText(
            f'{self.wcs_radesys}{wcs_equinox_str}')

        self.ui.minmax_widget.update_spinboxes_unit(f' {self.wcs_bunit}', 0, 1)

        self.ui.image_view.set_data_md(f' {self.wcs_bunit}', 0)
        self.ui.image_view.set_axis_md(' px', 0, 1, self.wcs_crpix1,
                                       self.wcs_crpix2)

        self.ui.zoom_view.set_data_md(f' {self.wcs_bunit}', 0)
        self.ui.zoom_view.set_axis_md(' px', 0, 1, self.wcs_crpix1,
                                      self.wcs_crpix2)

        self.on_relative_coord_checkbox_stateChanged(
            self.ui.relative_coord_checkbox.checkState())

        self.update_image_view()
        self.update_labels()

    def update_image_view(self) -> None:
        if self.img is None:
            return

        img_min, img_max = self.ui.minmax_widget.compute_min_max(
            self.img,
            self.cuts_actiongroup.checkedAction().data)

        self.saturation = self.img.max() / self.image_info['max']

        self.ui.image_view.setImage(
            self.img, img_min, img_max,
            self.scale_actiongroup.checkedAction().data)

        self.ui.colorbar.setTrueMinMax(self.img.min(), self.img.max())
        self.ui.colorbar.updateMinMax(img_min, img_max)

        self.update_zoom_view()

    def update_zoom_view(self) -> None:
        if self.img is None:
            return

        if self.zoomwindow_actiongroup.checkedAction(
        ).data == FollowMode.STAR and not np.isnan([self.star_x, self.star_y
                                                    ]).any():
            self.zoom_center_x = round(self.star_x)
            self.zoom_center_y = round(self.star_y)

        x = self.zoom_center_x
        y = self.zoom_center_y
        hw = self.zoom_half_width = self.img_width // self.zoom_level // 2
        hh = self.zoom_half_height = self.img_height // self.zoom_level // 2

        with QSignalBlocker(self.ui.x_spinbox):
            self.ui.x_spinbox.setValue(x - self.ui.image_view.axis_x_offset)

        with QSignalBlocker(self.ui.y_spinbox):
            self.ui.y_spinbox.setValue(y - self.ui.image_view.axis_y_offset)

        # with QSignalBlocker(self.ui.zoom_spinbox):
        #     self.ui.zoom_spinbox.setValue(self.zoom_level)
        #     self.update_zoom_spinbox_suffix()

        x = round(x)
        y = round(y)

        self.zoom_window.setRect(x - hw, y - hh, 2 * hw, 2 * hh)
        self.zoom_vertical_line.setLine(x, y - hh, x, y + hh)
        self.zoom_horizontal_line.setLine(x - hw, y, x + hw, y)

        zoom = image.cut(self.img, (2 * hw, 2 * hh), (x, y), overflow='cut')

        offset_x = max(x - hw, 0)
        offset_y = max(y - hh, 0)

        self.ui.zoom_view.setImage(
            zoom,
            self.ui.minmax_widget.ui.min_spinbox.value() /
            self.ui.minmax_widget.data_scaling,
            self.ui.minmax_widget.ui.max_spinbox.value() /
            self.ui.minmax_widget.data_scaling,
            self.scale_actiongroup.checkedAction().data,
            view=QRectF(x - hw, y - hh, 2 * hw,
                        2 * hh), offset=QPointF(offset_x, offset_y))

    def update_labels(self) -> None:
        if self.timestamp is None:
            self.ui.timestamp_label.updateText(timestamp='--')
        else:
            self.ui.timestamp_label.updateText(
                timestamp=self.timestamp.strftime('%H:%M:%S %d-%m-%Y'))

        self.ui.star_x_label.updateText(
            x=(self.star_x - self.ui.image_view.axis_x_offset) *
            self.ui.image_view.axis_scaling,
            axis_unit=self.ui.image_view.axis_unit,
            axis_precision=self.ui.image_view.axis_precision + 1,
        )

        self.ui.star_y_label.updateText(
            y=(self.star_y - self.ui.image_view.axis_y_offset) *
            self.ui.image_view.axis_scaling,
            axis_unit=self.ui.image_view.axis_unit,
            axis_precision=self.ui.image_view.axis_precision + 1,
        )

        self.ui.star_fwhm_label.updateText(
            fwhm=self.star_fwhm * self.ui.image_view.axis_scaling,
            axis_unit=self.ui.image_view.axis_unit,
            axis_precision=self.ui.image_view.axis_precision + 1,
        )

        self.ui.star_peak_label.updateText(
            peak=self.star_peak * self.ui.image_view.data_scaling,
            data_unit=self.ui.image_view.data_unit,
            data_precision=self.ui.image_view.data_precision,
        )

        if self.saturation >= 1:
            self.ui.saturation_label.setText('Saturated !')
            self.ui.saturation_label.setStyleSheet(
                f'color: {Color.RED.name()};')
        else:
            self.ui.saturation_label.updateText(saturation=self.saturation *
                                                100)
            self.ui.saturation_label.setStyleSheet('')

    # def update_zoom_spinbox_suffix(self) -> None:
    #     size_x = 2 * self.zoom_half_width * self.axis_scaling
    #     size_y = 2 * self.zoom_half_height * self.axis_scaling
    #     self.ui.zoom_spinbox.setSuffix(
    #         f'x ({size_x:.{self.axis_precision}f}{self.axis_unit} x {size_y:.{self.axis_precision}f}{self.axis_unit})'
    #     )

    ##### Coordinates transformation

    @Slot(int)
    def on_relative_coord_checkbox_stateChanged(self,
                                                state: Qt.CheckState) -> None:
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.ui.x_label.setText('ΔX')
            self.ui.y_label.setText('ΔY')
            self.ui.wcs_1_label.setText('Δ' + self.wcs_ctype1[0:3].strip('-'))
            self.ui.wcs_2_label.setText('Δ' + self.wcs_ctype2[0:3].strip('-'))
        else:
            self.ui.x_label.setText('X')
            self.ui.y_label.setText('Y')
            self.ui.wcs_1_label.setText(self.wcs_ctype1[0:3].strip('-'))
            self.ui.wcs_2_label.setText(self.wcs_ctype2[0:3].strip('-'))

    def norm_coordinates(self, ra: float, dec: float) -> [float, float]:
        if dec > 90:
            dec = 180 - dec
            ra = ra + 180
        elif dec < -90:
            dec = -180 - dec
            ra = ra + 180

        ra = ra % 360

        return ra, dec

    def update_world_coord_lineedit(self, lineedit: QLineEdit, value: float,
                                    unit: str, type: str, short: bool):
        if np.isnan(value):
            lineedit.setText('--')
        elif unit == 'deg':
            if type.startswith('RA--'):
                lineedit.setText(
                    kstring.sec_to_hms_str(value * 3600 / 15, decimal=1,
                                           short=short))
            else:
                lineedit.setText(
                    kstring.sec_to_dms_str(value * 3600, decimal=1,
                                           short=short))
        else:
            lineedit.setText(f'{value:f}{unit}')

    def update_coords(self, x, y):
        dx = x - self.wcs_crpix1
        dy = y - self.wcs_crpix2

        if self.ui.relative_coord_checkbox.isChecked():
            self.ui.x_spinbox.setValue(dx)
            self.ui.y_spinbox.setValue(dy)
        else:
            self.ui.x_spinbox.setValue(x)
            self.ui.y_spinbox.setValue(y)

        if self.wcs_cd11 != 0 or self.wcs_cd12 != 0 or self.wcs_cd21 != 0 or self.wcs_cd22 != 0:
            dl = self.wcs_cd11 * dx + self.wcs_cd12 * dy
            dm = self.wcs_cd21 * dx + self.wcs_cd22 * dy
        else:
            dl = self.wcs_pc11 * dx + self.wcs_pc12 * dy
            dm = self.wcs_pc21 * dx + self.wcs_pc22 * dy

            dl *= self.wcs_cdelt1
            dm *= self.wcs_cdelt2

        l = dl + self.wcs_crval1
        m = dm + self.wcs_crval2

        if self.ui.relative_coord_checkbox.isChecked():
            displayed_l = dl
            displayed_m = dm
            short = True
        else:
            if self.wcs_ctype1.startswith(
                    'RA--') and self.wcs_ctype2.startswith('DEC-'):
                displayed_l, displayed_m = self.norm_coordinates(l, m)
            elif self.wcs_ctype1.startswith(
                    'DEC-') and self.wcs_ctype2.startswith('RA--'):
                displayed_m, displayed_l = self.norm_coordinates(m, l)
            else:
                displayed_l, displayed_m = l, m

            short = False

        self.update_world_coord_lineedit(self.ui.wcs_1_lineedit, displayed_l,
                                         self.wcs_cunit1, self.wcs_ctype1,
                                         short)
        self.update_world_coord_lineedit(self.ui.wcs_2_lineedit, displayed_m,
                                         self.wcs_cunit2, self.wcs_ctype2,
                                         short)

    ##### Keywords table

    def update_keywords_table(self, header: fits.Header) -> None:
        self.keywords_model.update_data(header)

    @Slot(bool)
    def on_keywords_toolbutton_clicked(self, checked: bool) -> None:
        if checked:
            sizes = self.ui.keywords_splitter.sizes()

            self.ui.keywords_toolbutton.setArrowType(Qt.ArrowType.DownArrow)
            self.ui.keywords_widget.setVisible(True)
            self.resize(self.size().grownBy(
                QMargins(0, 0, 0, self.keywords_table_size)))

            self.ui.keywords_splitter.setSizes([
                sizes[0], sizes[1] + self.keywords_table_size
            ])

            self.ui.keywords_splitter.handle(1).setEnabled(True)
        else:
            sizes = self.ui.keywords_splitter.sizes()
            self.keywords_table_size = sizes[
                1] - self.ui.keywords_button_widget.height()

            self.ui.keywords_toolbutton.setArrowType(Qt.ArrowType.RightArrow)
            self.ui.keywords_widget.setVisible(False)

            self.resize(self.size().grownBy(
                QMargins(0, 0, 0, -self.keywords_table_size)))
            self.ui.keywords_splitter.setSizes([
                sizes[0], self.ui.keywords_button_widget.height()
            ])

            self.ui.keywords_splitter.handle(1).setEnabled(False)

    @Slot(str)
    def on_keywords_filter_lineedit_textEdited(self, text: str) -> None:
        self.filter_keywords()

    @Slot(int)
    def on_keywords_columns_combobox_currentIndexChanged(self,
                                                         index: int) -> None:
        self.filter_keywords()

    @Slot(int)
    def on_keywords_casesensitive_checkbox_stateChanged(
            self, state: Qt.CheckState) -> None:
        self.filter_keywords()

    def filter_keywords(self):
        text = self.ui.keywords_filter_lineedit.text()

        if text == '':
            self.keywords_proxymodel.setFilterRegularExpression('')
        else:
            if self.ui.keywords_casesensitive_checkbox.isChecked():
                case_senstitivity = Qt.CaseSensitivity.CaseSensitive
            else:
                case_senstitivity = Qt.CaseSensitivity.CaseInsensitive

            self.keywords_proxymodel.setFilterKeyColumn(
                self.ui.keywords_columns_combobox.currentIndex() - 1)
            self.keywords_proxymodel.setFilterCaseSensitivity(
                case_senstitivity)
            self.keywords_proxymodel.setFilterFixedString(text)

    ##### Window

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.file is None:
            self.backend.camera_image_updated.disconnect(
                self.camera_image_updated)

        return super().closeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        if self.file is None:
            self.backend.camera_image_updated.connect(
                self.camera_image_updated, Qt.ConnectionType.UniqueConnection)

        return super().showEvent(event)
