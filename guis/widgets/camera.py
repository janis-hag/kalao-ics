import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from PySide6.QtCore import QMarginsF, QPointF, QRectF, QTimer, Slot
from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox

from kalao.utils.image import LogScale

from guis.utils import colormaps
from guis.utils.definitions import Color
from guis.utils.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KMessageBox, KWidget
from guis.windows.fits_viewer import FITSViewerWindow

import config


def get_latest_image_path(path=config.FITS.science_data_storage, sort='db'):
    if sort == 'db':
        from kalao.utils import fits_handling

        return fits_handling.get_last_image_path()

    elif sort == 'symlink':
        return config.FITS.last_image

    folders = list(filter(lambda item: item.is_dir(), path.iterdir()))

    if sort == 'time':
        latest_folder = max(folders, key=lambda item: item.stat().st_ctime)
        files = latest_folder.glob('*')
        latest_file = max(files, key=lambda item: item.stat().st_ctime)

        return latest_file

    elif sort == 'name':
        latest_folder = max(folders)
        files = latest_folder.glob('*')
        latest_file = max(files)

        return latest_file


class CameraWidget(KWidget, MinMaxMixin, SceneHoverMixin, BackendDataMixin):
    image_info = config.Images.fli

    data_unit = ' ADU'
    data_precision = 0
    data_center_x = config.Camera.center_x
    data_center_y = config.Camera.center_y

    axis_unit = ' px'
    axis_precision = 0
    axis_scaling = 1

    WFS_fov = 4 * config.WFS.plate_scale / config.Camera.plate_scale

    fits_viewer = None

    saturation = np.nan
    timestamp = None

    hdul = None

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('camera.ui', self)
        self.resize(600, 400)

        self.init_minmax(self.camera_view)

        self.camera_view.setView(self.image_info['shape'])

        self.camera_view.setMargins(QMarginsF(40, 30, 40, 30))

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        pen = QPen(Color.BLUE, 1.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.roi = self.camera_view.scene().addEllipse(
            self.data_center_x - self.WFS_fov / 2, self.data_center_y -
            self.WFS_fov / 2, self.WFS_fov, self.WFS_fov, pen)
        self.roi.setZValue(1)

        self.update_labels()

        self.camera_view.hovered.connect(self.hover_xyv_to_str)
        backend.all_updated.connect(self.all_updated)
        backend.camera_image_updated.connect(self.camera_image_updated)

    def all_updated(self, data):
        mtime = self.consume_fits_mtime(data, config.FITS.last_image_all)
        if mtime is not None:
            QTimer.singleShot(0, self, self.backend.camera_image)

        centering_manual_flag = self.consume_dict(data, 'memory',
                                                  'centering_manual_flag')
        if centering_manual_flag is not None:
            if centering_manual_flag is True:
                self.open_fits_viewer()
                if self.fits_viewer is not None:
                    self.fits_viewer.enter_manual_centering()
            elif centering_manual_flag is False:
                if self.fits_viewer is not None:
                    self.fits_viewer.exit_manual_centering()

    def camera_image_updated(self, data):
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

            img_min, img_max = self.compute_min_max(img)

            self.saturation = img.max() / self.image_info['max']

            # View is full image size
            view = QRectF(0, 0, self.image_info['shape'][1],
                          self.image_info['shape'][0])
            offset = QPointF(hdul[0].header['HIERARCH ESO DET WIN1 STRX'] - 1 -
                             hdul[0].header['HIERARCH ESO DET OUT1 PRSCX'],
                             hdul[0].header['HIERARCH ESO DET WIN1 STRY'] - 1 -
                             hdul[0].header['HIERARCH ESO DET OUT1 PRSCY']
                             )  # Note: FITS indexing starts at 1

            self.camera_view.setImage(img, img_min, img_max, scale=LogScale,
                                      view=view, offset=offset)

            self.update_labels()

    def update_labels(self):
        if self.timestamp is None:
            self.timestamp_label.updateText(timestamp='--')
        else:
            self.timestamp_label.updateText(
                timestamp=self.timestamp.strftime('%H:%M:%S %d-%m-%Y'))

        if self.saturation >= 1:
            self.saturation_label.setText('Saturated !')
            self.saturation_label.setStyleSheet(f'color: {Color.RED.name()};')
        else:
            self.saturation_label.updateText(saturation=self.saturation * 100)
            self.saturation_label.setStyleSheet('')

    def change_units(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.axis_unit = '"'
            self.axis_precision = 1
            self.axis_scaling = config.Camera.plate_scale
        else:
            self.axis_unit = ' px'
            self.axis_precision = 0
            self.axis_scaling = 1

        self.update_labels()

        ticks_x = []
        ticks_y = []
        for xy in [-400, -300, -200, -100, 0, 100, 200, 300, 400]:
            tick_label = f'{xy*self.axis_scaling:.{self.axis_precision}f}'
            tick_pos_x = xy + self.data_center_x
            tick_pos_y = xy + self.data_center_y

            ticks_x.append((tick_pos_x, tick_label))
            ticks_y.append((tick_pos_y, tick_label))

        self.camera_view.setTickParams(0, 5, 5, 10, ticks_x, ticks_y)

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.camera_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.camera_view.updateColormap(colormaps.BlackBody())

    @Slot(bool)
    def on_open_button_clicked(self, checked):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter('Images (*.fits)')
        dialog.setAcceptMode(QFileDialog.AcceptOpen)

        if config.FITS.science_data_storage.exists():
            dialog.setDirectory(str(config.FITS.science_data_storage))

        error_dialog = KMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
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

                    FITSViewerWindow(self.backend, file=filename, parent=self)
                except PermissionError:
                    error_list.append(
                        f'{filename.name}: Can\'t read file, permission refused.'
                    )

            if len(error_list) > 0:
                error_dialog.setInformativeText('\n'.join(error_list))
                error_dialog.show()

    @Slot(bool)
    def on_ds9_button_clicked(self, checked):
        subprocess.Popen(['ds9', get_latest_image_path(sort='symlink')])

    @Slot(bool)
    def on_fits_viewer_button_clicked(self, checked):
        self.open_fits_viewer()

    def open_fits_viewer(self):
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

            self.fits_viewer = FITSViewerWindow(
                self.backend, hdul, on_sky_unit=(self.axis_unit == '"'),
                parent=self)
