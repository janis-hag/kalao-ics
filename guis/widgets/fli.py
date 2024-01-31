from pathlib import Path
from subprocess import Popen

import numpy as np

from PySide6.QtCore import Slot
from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox

from kalao.utils.image import LogScale

from guis.utils import colormaps
from guis.utils.definitions import Color
from guis.utils.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KMessageBox, KWidget
from guis.windows.fli_zoom import FLIZoomWindow

import config


def get_latest_image_path(path=config.FITS.science_data_storage, sort='db'):
    if sort == 'db':
        from kalao.utils import file_handling

        return file_handling.get_last_image_path()

    elif sort == 'symlink':
        return config.FITS.last_image

    folders = list(filter(lambda item: item.is_dir(), path.iterdir()))

    if sort == 'time':
        latest_folder = max(folders, key=lambda item: item.stat().st_ctime)
        files = latest_folder.glob("*")
        latest_file = max(files, key=lambda item: item.stat().st_ctime)

        return latest_file

    elif sort == 'name':
        latest_folder = max(folders)
        files = latest_folder.glob("*")
        latest_file = max(files)

        return latest_file


class FLIWidget(KWidget, MinMaxMixin, SceneHoverMixin, BackendDataMixin):
    associated_stream = config.Streams.FLI
    stream_info = config.StreamInfo.fli_stream

    data_unit = ' ADU'
    data_precision = 0
    data_center_x = config.FLI.center_x
    data_center_y = config.FLI.center_y

    axis_unit = ' px'
    axis_precision = 0
    axis_scaling = 1

    tick_fontsize = 10
    tick_spacing = 10
    tick_tick_length = 10
    tick_text_spacing = 5

    WFS_fov = 4 * config.WFS.plate_scale / config.FLI.plate_scale

    zoom_window = None

    saturation = np.nan
    timestamp = None
    star_x = np.nan
    star_y = np.nan
    star_peak = np.nan
    star_fwhm = np.nan

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('fli.ui', self)
        self.resize(600, 400)

        self.init_minmax(self.fli_view)

        self.fli_view.setView(self.stream_info['shape'])

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        pen = QPen(Color.BLUE, 1.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.roi = self.fli_view.scene.addEllipse(
            self.data_center_x - self.WFS_fov / 2, self.data_center_y -
            self.WFS_fov / 2, self.WFS_fov, self.WFS_fov, pen)
        self.roi.setZValue(1)

        self.update_labels()

        self.fli_view.hovered.connect(self.hover_xyv_to_str)
        backend.all_updated.connect(self.all_updated)
        backend.streams_fli_updated.connect(self.streams_fli_updated)

    def all_updated(self, data):
        cnt = self.consume_stream_cnt(data, config.Streams.FLI)
        if cnt != None:
            self.backend.get_streams_fli()

        centering_manual_v, centering_manual_t = self.consume_db(
            data, 'obs', 'centering_manual')
        if centering_manual_v is not None:
            if centering_manual_v is True:
                self.open_zoom_window()
                if self.zoom_window is not None:
                    self.zoom_window.enter_manual_centering()
            elif centering_manual_v is False:
                if self.zoom_window is not None:
                    self.zoom_window.exit_manual_centering()

    def streams_fli_updated(self, data):
        img = self.consume_stream(data, config.Streams.FLI)

        if img is not None:
            #self.fli_view.addNEIndicator(parang from keywords)

            img_min, img_max = self.compute_min_max(img)

            self.saturation = img.max() / self.stream_info['max']

            self.fli_view.setImage(img, img_min, img_max, scale=LogScale)

            # self.star_x, self.star_y, self.star_peak, self.star_fwhm = find_star_fast(
            #     img)

            self.update_labels()

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

    def change_units(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.axis_scaling = config.FLI.plate_scale
            self.axis_unit = '"'
            self.axis_precision = 1
        else:
            self.axis_scaling = 1
            self.axis_unit = ' px'
            self.axis_precision = 0

        self.update_labels()

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

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.fli_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.fli_view.updateColormap(colormaps.BlackBody())

    @Slot(bool)
    def on_open_button_clicked(self, checked):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter('Images (*.fits)')
        dialog.setAcceptMode(QFileDialog.AcceptOpen)

        error_dialog = KMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setModal(False)
        error_dialog.setText("<b>FITS loading failed!</b>")

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

                    FLIZoomWindow(self.backend, file=filename, parent=self)
                except PermissionError:
                    error_list.append(
                        f'{filename.name}: Can\'t read file, permission refused.'
                    )

            if len(error_list) > 0:
                error_dialog.setInformativeText('\n'.join(error_list))
                error_dialog.show()

    @Slot(bool)
    def on_ds9_button_clicked(self, checked):
        Popen(['ds9', get_latest_image_path(sort='symlink')])

    @Slot(bool)
    def on_zoom_window_button_clicked(self, checked):
        self.open_zoom_window()

    def open_zoom_window(self):
        if self.zoom_window is not None:
            self.zoom_window.show()
            self.zoom_window.activateWindow()

            if self.fli_view.img is not None:
                self.zoom_window.update_fli_view(self.fli_view.img.copy())
        else:
            if self.fli_view.img is not None:
                img = self.fli_view.img.copy()
            else:
                img = None

            self.zoom_window = FLIZoomWindow(
                self.backend, img, on_sky_unit=(self.axis_unit == '"'),
                parent=self)
