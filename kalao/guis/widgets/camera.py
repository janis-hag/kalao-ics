from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from PySide6.QtCore import QMarginsF, QPointF, QRectF, QTimer, Signal, Slot
from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from compiled.ui_camera import Ui_CameraWidget

from kalao.common.image import LogScale

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils import colormaps
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.widgets import KMessageBox, KWidget
from kalao.guis.windows.fits_viewer import FITSViewerWindow

import config


class CameraWidget(KWidget, BackendDataMixin):
    image_info = config.Images.fli

    WFS_fov = 4 * config.WFS.plate_scale / config.Camera.plate_scale

    fits_viewer = None

    saturation = np.nan
    img_max = np.nan
    timestamp = None

    hdul = None

    hovered = Signal(str)

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend

        self.ui = Ui_CameraWidget()
        self.ui.setupUi(self)

        self.resize(600, 400)

        self.ui.minmax_widget.setup(self.ui.camera_view, ' ADU', 0, 1, -999999,
                                    999999, self.image_info['min'],
                                    self.image_info['max'])
        self.ui.camera_view.set_data_md(' ADU', 0)
        self.ui.camera_view.set_axis_md(' px', 0, 1, config.Camera.center_x,
                                        config.Camera.center_y)

        self.ui.camera_view.setView(self.image_info['shape'])

        self.ui.camera_view.setMargins(QMarginsF(40, 30, 40, 30))

        self.change_units(Qt.CheckState.Unchecked)
        self.change_colormap(Qt.CheckState.Unchecked)

        ticks_x = np.array([-400, -300, -200, -100, 0, 100, 200, 300, 400
                            ]) + config.Camera.center_x
        ticks_y = np.array([-400, -300, -200, -100, 0, 100, 200, 300, 400
                            ]) + config.Camera.center_y
        self.ui.camera_view.setTickParams(0, 5, 5, 10, ticks_x, ticks_y)

        pen = QPen(Color.BLUE, 1.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        self.roi = self.ui.camera_view.scene().addEllipse(
            self.ui.camera_view.axis_x_offset - self.WFS_fov / 2,
            self.ui.camera_view.axis_y_offset - self.WFS_fov / 2, self.WFS_fov,
            self.WFS_fov, pen)
        self.roi.setZValue(1)

        self.update_labels()

        self.ui.camera_view.hovered_str.connect(lambda string: self.hovered.
                                                emit(string))
        backend.all_updated.connect(self.all_updated)
        backend.camera_image_updated.connect(self.camera_image_updated)

    def all_updated(self, data: dict[str, Any]) -> None:
        mtime = self.consume_fits_mtime(data, config.FITS.last_image_all)
        if mtime is not None:
            QTimer.singleShot(0, self.backend, self.backend.camera_image)

        centering_manual_flag = self.consume_dict(data, 'centering_manual',
                                                  'flag')
        if centering_manual_flag is not None:
            if centering_manual_flag is True:
                centering_manual_reason = self.consume_dict(
                    data, 'centering_manual', 'reason', force=True)

                self.open_fits_viewer()
                if self.fits_viewer is not None:
                    self.fits_viewer.enter_manual_centering(
                        reason=centering_manual_reason)
            elif centering_manual_flag is False:
                if self.fits_viewer is not None:
                    self.fits_viewer.exit_manual_centering()

    def camera_image_updated(self, data: dict[str, Any]) -> None:
        hdul = self.consume_fits_full(data, config.FITS.last_image_all)

        if hdul is not None:
            self.hdul = hdul

            if hdul[0].data is None:
                return
            elif len(hdul[0].data.shape) == 2:
                img = hdul[0].data
            elif len(hdul[0].data.shape) == 3:
                img = hdul[0].data[-1, :, :]
            else:
                raise Exception('Unexpected shape for camera image')

            self.timestamp = datetime.fromisoformat(
                hdul[0].header['DATE']).replace(
                    tzinfo=timezone.utc).astimezone()

            # self.camera_view.setNEIndicator(parang from keywords)

            img_min, img_max = self.ui.minmax_widget.compute_min_max(img)

            self.saturation = img.max() / self.image_info['max']
            self.img_max = img.max()

            # View is full image size
            view = QRectF(0, 0, self.image_info['shape'][1],
                          self.image_info['shape'][0])
            offset = QPointF(hdul[0].header['HIERARCH ESO DET WIN1 STRX'] - 1 -
                             hdul[0].header['HIERARCH ESO DET OUT1 PRSCX'],
                             hdul[0].header['HIERARCH ESO DET WIN1 STRY'] - 1 -
                             hdul[0].header['HIERARCH ESO DET OUT1 PRSCY']
                             )  # Note: FITS indexing starts at 1

            self.ui.camera_view.setImage(img, img_min, img_max, scale=LogScale,
                                         view=view, offset=offset)

            self.update_labels()

    def update_labels(self) -> None:
        if self.timestamp is None:
            self.ui.timestamp_label.updateText(timestamp='--')
        else:
            self.ui.timestamp_label.updateText(
                timestamp=self.timestamp.strftime('%H:%M:%S %d-%m-%Y'))

        if self.saturation >= 1:
            self.ui.saturation_label.setText('Saturated !')
            self.ui.saturation_label.setStyleSheet(
                f'color: {Color.RED.name()};')
        else:
            self.ui.saturation_label.updateText(saturation=self.saturation *
                                                100)
            self.ui.saturation_label.setStyleSheet('')

        if self.img_max > config.Camera.linear_range_max:
            self.ui.linearity_label.setText('Outside of linear range')
            self.ui.linearity_label.setStyleSheet(
                f'color: {Color.RED.name()};')
        else:
            self.ui.linearity_label.setText('Inside of linear range')
            self.ui.linearity_label.setStyleSheet('')

    def change_units(self, state: Qt.CheckState) -> None:
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.ui.camera_view.set_axis_md('"', 1, config.Camera.plate_scale,
                                            config.Camera.center_x,
                                            config.Camera.center_y)
        else:
            self.ui.camera_view.set_axis_md(' px', 0, 1,
                                            config.Camera.center_x,
                                            config.Camera.center_y)

        self.update_labels()

    def change_colormap(self, state: Qt.CheckState) -> None:
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.ui.camera_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.ui.camera_view.updateColormap(colormaps.BlackBody())

    @Slot(bool)
    def on_open_button_clicked(self, checked: bool) -> None:
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilter('Images (*.fits)')
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)

        if config.FITS.science_data_storage.exists():
            dialog.setDirectory(str(config.FITS.science_data_storage))

        error_dialog = KMessageBox(self)
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setModal(True)
        error_dialog.setText('<b>FITS loading failed!</b>')

        if dialog.exec():
            filenames = dialog.selectedFiles()

            if len(filenames) == 0:
                error_dialog.setInformativeText(
                    f'Select at least one file (got {len(filenames)}).')
                error_dialog.show()
                return

            error_list = []
            for filename in filenames:
                filename = Path(filename)
                try:
                    if not filename.exists():
                        error_list.append(
                            f'{filename.name}: File does not exists.')
                        continue

                    if filename.suffix.lower() != '.fits':
                        error_list.append(
                            f'{filename.name}: Unsupported file extension "{filename.suffix}".'
                        )
                        continue

                    FITSViewerWindow(self.backend, file=filename)
                except PermissionError:
                    error_list.append(
                        f'{filename.name}: Can\'t read file, permission refused.'
                    )

            if len(error_list) > 0:
                error_dialog.setInformativeText('\n'.join(error_list))
                error_dialog.show()

    @Slot(bool)
    def on_fits_viewer_button_clicked(self, checked: bool) -> None:
        self.open_fits_viewer()

    def open_fits_viewer(self) -> None:
        if self.fits_viewer is not None:
            self.fits_viewer.show()
            self.fits_viewer.activateWindow()

            if self.hdul is not None:
                self.fits_viewer.update_image(self.hdul.copy())
        else:
            if self.hdul is not None:
                hdul = self.hdul.copy()
            else:
                hdul = None

            self.fits_viewer = FITSViewerWindow(self.backend, hdul)
