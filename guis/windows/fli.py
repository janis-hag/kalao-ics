from subprocess import Popen

import numpy as np

from PySide6.QtCore import Slot
from PySide6.QtGui import QPen, Qt

from guis.kalao import colormaps
from guis.kalao.definitions import Color
from guis.kalao.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget
from guis.windows.fli_zoom import FLIZoomWindow

import config


def get_latest_image_path(path=config.FITS.science_data_storage, sort='db'):
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

    elif sort == 'db':
        from kalao.utils import file_handling

        return file_handling.get_last_image_path()


class FLIWidget(KalAOWidget, MinMaxMixin, SceneHoverMixin, BackendDataMixin):
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

        self.star_label.updateText(x=np.nan, y=np.nan, peak=np.nan,
                                   fwhm=np.nan, precision=np.nan,
                                   data_unit=self.data_unit,
                                   axis_unit=self.axis_unit)

        self.parang = 0

        self.fli_view.hovered.connect(self.hover_xyv_to_str)
        backend.data_updated.connect(self.data_updated)
        backend.fli_updated.connect(self.fli_updated)

    def data_updated(self, data):
        cnt = self.consume_stream_cnt(data, config.Streams.FLI)
        if cnt != None:
            self.backend.get_streams_fli()

    def fli_updated(self, data):
        img = self.consume_stream(data, config.Streams.FLI)

        if img is not None:
            self.parang = (self.parang + 5) % 360
            self.fli_view.addParang(self.parang)

            img_min, img_max = self.compute_min_max(img)

            self.fli_view.setImage(img, img_min, img_max)

            #x, y, peak, fwhm = starfinder.find_star(img) #TODO
            x, y, peak, fwhm = np.nan, np.nan, np.nan, np.nan

            self.star_label.updateText(x=x * self.axis_scaling,
                                       y=y * self.axis_scaling,
                                       peak=peak * self.data_scaling,
                                       fwhm=fwhm * self.axis_scaling,
                                       precision=self.axis_precision,
                                       data_unit=self.data_unit,
                                       axis_unit=self.axis_unit)

    def change_units(self, state):
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

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.fli_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.fli_view.updateColormap(colormaps.BlackBody())

    @Slot(bool)
    def on_ds9_button_clicked(self, checked):
        Popen(['ds9', get_latest_image_path()])

    @Slot(bool)
    def on_zoom_window_button_clicked(self, checked):
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

            self.zoom_window = FLIZoomWindow(self.backend, img)
