from subprocess import Popen

import numpy as np

from PySide2.QtGui import QFont, QPen, Qt
from PySide2.QtWidgets import QGraphicsItem

from guis.kalao import colormaps
from guis.kalao.definitions import Color
from guis.kalao.mixins import HoverMixin, MinMaxMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget, OffsetedTextItem
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


class FLIWidget(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = config.Streams.FLI
    stream_info = config.StreamInfo.fli_stream
    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0
    axis_scaling = 1

    tick_fontsize = 10
    tick_spacing = 10
    tick_tick_length = 10
    tick_text_spacing = 5
    tick_nb = 9
    tick_labels = []

    data_center_x = config.FLI.center_x
    data_center_y = config.FLI.center_y
    WFS_fov = 4 * config.WFS.plate_scale / config.FLI.plate_scale
    ticks_pos = [-400, -300, -200, -100, 0, 100, 200, 300, 400]

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('fli.ui', self)
        self.resize(600, 400)

        MinMaxMixin.__init__(self)

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        pen = QPen(Color.BLUE, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.roi = self.fli_view.scene.addEllipse(
            self.data_center_x - self.WFS_fov / 2, self.data_center_y -
            self.WFS_fov / 2, self.WFS_fov, self.WFS_fov, pen)
        self.roi.setZValue(1)

        self.addTicks()

        self.ds9_button.clicked.connect(self.open_ds9)
        self.zoom_window_button.clicked.connect(self.open_zoom_window)

        self.fli_view.hovered.connect(self.hover_event)
        backend.updated.connect(self.data_updated)

    def addTicks(self):
        self.fli_view.margins = (
            self.tick_spacing + self.tick_tick_length +
            self.tick_text_spacing + 4 * self.tick_fontsize + 100,
            self.tick_spacing + self.tick_tick_length +
            self.tick_text_spacing + 4 * self.tick_fontsize,
            self.tick_spacing + self.tick_tick_length +
            self.tick_text_spacing + 4 * self.tick_fontsize + 100,
            self.tick_spacing + self.tick_tick_length +
            self.tick_text_spacing + 4 * self.tick_fontsize)

        width = self.stream_info['shape'][1]
        height = self.stream_info['shape'][0]

        pen = QPen(Color.BLACK, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.addVerticalTicks(0, height, -(self.tick_spacing),
                              -(self.tick_spacing + self.tick_tick_length),
                              pen)
        self.addVerticalTicks(
            0, height, width + self.tick_spacing,
            width + self.tick_spacing + self.tick_tick_length, pen)

        self.addHorizontalTicks(0, width, -(self.tick_spacing),
                                -(self.tick_spacing + self.tick_tick_length),
                                pen)
        self.addHorizontalTicks(
            0, width, height + self.tick_spacing,
            height + self.tick_spacing + self.tick_tick_length, pen)

        self.addTicksLabels()

    def addVerticalTicks(self, start, end, tick_start, tick_end, pen):
        self.fli_view.scene.addLine(tick_start, start, tick_start, end, pen)

        for y in self.ticks_pos:
            self.fli_view.scene.addLine(tick_start, y + self.data_center_y,
                                        tick_end, y + self.data_center_y, pen)

    def addHorizontalTicks(self, start, end, tick_start, tick_end, pen):
        self.fli_view.scene.addLine(start, tick_start, end, tick_start, pen)

        for x in self.ticks_pos:
            self.fli_view.scene.addLine(x + self.data_center_x, tick_start,
                                        x + self.data_center_x, tick_end, pen)

    def addTicksLabels(self):
        for text_item in self.tick_labels:
            self.fli_view.scene.removeItem(text_item)

        self.tick_labels = []

        width = self.stream_info['shape'][1]
        height = self.stream_info['shape'][0]

        font = QFont()
        font.setPixelSize(self.tick_fontsize)

        self.addVerticalTickLabels(
            0, height, width + self.tick_spacing + self.tick_tick_length +
            self.tick_text_spacing, font)
        self.addHorizontalTickLabels(
            0, width, height + self.tick_spacing + self.tick_tick_length +
            self.tick_text_spacing, font)

    def addVerticalTickLabels(self, start, end, text_start, font):
        for y in self.ticks_pos:
            pos = y * self.axis_scaling

            text_item = OffsetedTextItem(f'{pos:.1f}'.rstrip('0').rstrip('.'))
            text_item.setFont(font)
            text_item.setPos(text_start, y + self.data_center_y)
            text_item.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            self.fli_view.scene.addItem(text_item)

            probe = OffsetedTextItem(
                f'{-abs(pos):.1f}'.rstrip('0').rstrip('.'))
            probe.setFont(font)
            probe.setFlag(QGraphicsItem.ItemIgnoresTransformations)

            self.fli_view.scene.addItem(probe)
            text_item.setOffset(
                text_item.boundingRect().width() -
                probe.boundingRect().width(),
                text_item.boundingRect().height() / 2)
            self.fli_view.scene.removeItem(probe)

            self.tick_labels.append(text_item)

    def addHorizontalTickLabels(self, start, end, text_start, font):
        for x in self.ticks_pos:
            pos = x * self.axis_scaling

            text_item = OffsetedTextItem(f'{pos:.1f}'.rstrip('0').rstrip('.'))
            text_item.setFont(font)
            text_item.setPos(x + self.data_center_x, text_start)
            text_item.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            self.fli_view.scene.addItem(text_item)

            probe = OffsetedTextItem(f'{abs(pos):.1f}'.rstrip('0').rstrip('.'))
            probe.setFont(font)
            probe.setFlag(QGraphicsItem.ItemIgnoresTransformations)

            self.fli_view.scene.addItem(probe)
            text_item.setOffset(
                text_item.boundingRect().width() -
                probe.boundingRect().width() / 2, 0)
            self.fli_view.scene.removeItem(probe)

            self.tick_labels.append(text_item)

    def data_updated(self):
        img = self.backend.data['fli_stream']['stream']

        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.fli_view.setImage(img, img_min, img_max)

        #x, y, peak, fwhm = starfinder.find_star(img)
        x, y, peak, fwhm = np.nan, np.nan, np.nan, np.nan

        self.star_label.updateText(x=x * self.axis_scaling,
                                   y=y * self.axis_scaling, peak=peak,
                                   fwhm=fwhm * self.axis_scaling,
                                   precision=self.axis_precision)

    def change_units(self, state):
        if state == Qt.Checked:
            self.axis_scaling = config.FLI.plate_scale
            self.axis_unit = ' asec'
            self.axis_precision = 1
        else:
            self.axis_scaling = 1
            self.axis_unit = ' px'
            self.axis_precision = 0

        self.addTicksLabels()
        self.update_spinboxes_unit()

    def change_colormap(self, state):
        if state == Qt.Checked:
            self.fli_view.setColormap(colormaps.GrayscaleSaturation())
        else:
            self.fli_view.setColormap(colormaps.BlackBody())

    def open_ds9(self, checked):
        Popen(['ds9', get_latest_image_path()])

    def open_zoom_window(self, checked):
        self.zoom_window = FLIZoomWindow(self.fli_view.img.copy())
