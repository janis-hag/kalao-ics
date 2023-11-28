import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
from signal import SIGINT, signal
from subprocess import Popen

import numpy as np

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QDateTime, QPointF, QTimer
from PySide2.QtGui import QFont, QPen, Qt, QTextCursor
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QCheckBox, QGraphicsItem

from kalao.utils import kalao_time, kalao_tools

from guis.backends.local import LocalBackend, LocalLogsThread
from guis.backends.simulation import SimulationBackend, SimulationLogsThread
from guis.kalao import colormaps
from guis.kalao.definitions import Color, Logo
from guis.kalao.mixins import HoverMixin, MinMaxMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import (KalAOChart, KalAOGraphicsView, KalAOLabel,
                                KalAOMainWindow, KalAOSvgWidget, KalAOWidget,
                                OffsetedTextItem)

from kalao.definitions.enums import LogType

import config

Streams = config.Streams

streams = {}

ui_path = Path(__file__).absolute().parent


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


class WFSWidget(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = Streams.NUVU
    stream_info = config.StreamInfo.nuvu_stream
    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi(ui_path / 'ui/wfs.ui', self)
        self.resize(600, 400)

        MinMaxMixin.__init__(self)

        self.change_colormap(Qt.Unchecked)

        if self.stream_info['shape'] == (128, 128):
            self.subaps_size = 10
            self.subaps_offset = 10
            self.subaps_pitch = 10
        elif self.stream_info['shape'] == (64, 64):
            self.subaps_size = 4
            self.subaps_offset = 5
            self.subaps_pitch = 5

        # Add grid to window
        self.rois = {}
        for i in config.AO.all_subaps:
            j, k = kalao_tools.get_subaperture_2d(i)

            if i in config.AO.masked_subaps:
                color = Color.DARK_GREY
            else:
                color = Color.BLUE

            pen = QPen(color, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
            pen.setCosmetic(True)

            roi = self.wfs_view.scene.addRect(
                self.subaps_pitch * k + self.subaps_offset,
                self.subaps_pitch * j + self.subaps_offset, self.subaps_size,
                self.subaps_size, pen)
            roi.setZValue(1)
            self.rois[i] = roi

        self.wfs_view.hovered.connect(self.hover_event)
        backend.updated.connect(self.update_data)

    def update_data(self):
        img = self.backend.data['nuvu_stream']['data']

        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.wfs_view.setImage(img, img_min, img_max)

    def change_colormap(self, state):
        if state == Qt.Checked:
            self.wfs_view.colormap = colormaps.GrayscaleSaturation()
        else:
            self.wfs_view.colormap = colormaps.BlackBody()

    subap_current = None

    def hover_event(self, x, y, v):
        #self.tooltip= QToolTip()

        pen = QPen(Color.GREEN, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        if x != -1 and y != -1:
            string = f'X: {(x-self.data_center_x)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, Y: {(y-self.data_center_y)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, V: {v:.{self.data_precision}f}{self.data_unit}'

            subap = kalao_tools.subap_at(x, y)
            if subap is not None:
                self.reset_subap_color()

                self.subap_current = subap
                self.subap_previous_pen = self.rois[subap].pen()
                self.rois[subap].setPen(pen)

                #i,j = kalao_tools.get_subaperture_2d(subap)
                #self.tooltip.showText(QPoint(screenPos.x(), screenPos.y()), f'Subap: {subap} ({i},{j})\nX: 1\nY: 1\nValue: {img[y,x]}\nFlux\nSlope')
            else:
                self.reset_subap_color()
                #self.tooltip.hideText()

            self.hovered.emit(string)
        else:
            self.reset_subap_color()
            #self.tooltip.hideText()

            self.hovered.emit('')

    def reset_subap_color(self):
        if self.subap_current is not None:
            self.rois[self.subap_current].setPen(self.subap_previous_pen)

            self.subap_current = None
            self.subap_previous_pen = None


class FLIWidget(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = Streams.FLI
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

        loadUi(ui_path / 'ui/fli.ui', self)
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

        self.fli_view.hovered.connect(self.hover_event)
        backend.updated.connect(self.update_data)

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

    def update_data(self):
        img = self.backend.data['fli_stream']['data']

        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.fli_view.setImage(img, img_min, img_max)

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
            self.fli_view.colormap = colormaps.GrayscaleSaturation()
        else:
            self.fli_view.colormap = colormaps.BlackBody()

    def open_ds9(self, checked):
        Popen(['ds9', get_latest_image_path()])


class SlopesWidget(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = Streams.SLOPES
    stream_info = config.StreamInfo.shwfs_slopes
    data_unit = ' px'
    data_precision = 3

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi(ui_path / 'ui/slopes.ui', self)
        self.resize(600, 400)

        MinMaxMixin.__init__(self)

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        self.slopes_view.hovered.connect(self.hover_event)
        backend.updated.connect(self.update_data)

    def update_data(self):
        img = self.backend.data['shwfs_slopes']['data'] * self.data_scaling
        tip = self.backend.data['shwfs_slopes']['tip'] * self.data_scaling
        tilt = self.backend.data['shwfs_slopes']['tilt'] * self.data_scaling
        residual = self.backend.data['shwfs_slopes'][
            'residual'] * self.data_scaling

        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            abs_max = max(abs(img_min), abs(img_max))
            img_min = -abs_max
            img_max = abs_max

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.slopes_view.setImage(img, img_min, img_max)

        self.tip_label.updateText(tip=tip, unit=self.data_unit)
        self.tilt_label.updateText(tilt=tilt, unit=self.data_unit)
        self.residual_label.updateText(residual=residual, unit=self.data_unit)

    def change_units(self, state):
        if state == Qt.Checked:
            self.data_unit = ' asec'
            self.data_scaling = config.WFS.plate_scale
        else:
            self.data_unit = ' px'
            self.data_scaling = 1

        self.update_spinboxes_unit()

    def change_colormap(self, state):
        if state == Qt.Checked:
            self.slopes_view.colormap = colormaps.GrayscaleSaturation()
        else:
            self.slopes_view.colormap = colormaps.CoolWarm()


class FluxWidget(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = Streams.FLUX
    stream_info = config.StreamInfo.shwfs_slopes_flux
    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi(ui_path / 'ui/flux.ui', self)
        self.resize(600, 400)

        MinMaxMixin.__init__(self)

        self.change_colormap(Qt.Unchecked)

        self.flux_view.hovered.connect(self.hover_event)
        backend.updated.connect(self.update_data)

    def update_data(self):
        img = self.backend.data['shwfs_slopes_flux']['data']
        flux_avg = self.backend.data['shwfs_slopes_flux'][
            'flux_subaperture_avg']
        flux_brightest = self.backend.data['shwfs_slopes_flux'][
            'flux_subaperture_brightest']

        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.flux_view.setImage(img, img_min, img_max)

        self.flux_avg_label.updateText(flux_avg=flux_avg, unit=self.data_unit)
        self.flux_brightest_label.updateText(flux_brightest=flux_brightest,
                                             unit=self.data_unit)

    def change_colormap(self, state):
        if state == Qt.Checked:
            self.flux_view.colormap = colormaps.GrayscaleSaturation()
        else:
            self.flux_view.colormap = colormaps.BlackBody()


class DMWidget(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = Streams.DM
    stream_info = config.StreamInfo.dm01disp
    data_unit = ' um'
    data_precision = 3

    axis_unit = ' px'
    axis_precision = 0

    #TODO: modify stream_info with stroke_max?

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi(ui_path / 'ui/dm.ui', self)
        self.resize(600, 400)

        MinMaxMixin.__init__(self)

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        self.dm_view.hovered.connect(self.hover_event)
        backend.updated.connect(self.update_data)

    def update_data(self):
        img = self.backend.data['dm01disp']['data'] * self.data_scaling
        max_stroke = self.backend.data['dm01disp'][
            'max_stroke'] * self.data_scaling

        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            abs_max = max(abs(img_min), abs(img_max))
            img_min = -abs_max
            img_max = abs_max

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.dm_view.setImage(img, img_min, img_max)

        stroke_max = np.max(img)
        stroke_min = np.min(img)
        stroke_raw = stroke_max - stroke_min
        stroke_effective = min(stroke_max, 1.75 * max_stroke) - max(
            stroke_min, -1.75 * max_stroke)

        self.stroke_raw_label.updateText(stroke_raw=stroke_raw,
                                         unit=self.data_unit)
        self.stroke_effective_label.updateText(
            stroke_effective=stroke_effective, unit=self.data_unit)

    def change_units(self, state):
        if state == Qt.Checked:
            self.data_unit = ' um'
            self.data_scaling = 2
        else:
            self.data_unit = ' um'
            self.data_scaling = 1

        self.update_spinboxes_unit()

    def change_colormap(self, state):
        if state == Qt.Checked:
            self.dm_view.colormap = colormaps.GrayscaleSaturation()
        else:
            self.dm_view.colormap = colormaps.CoolWarm()


class TTMWidget(KalAOWidget, MinMaxMixin):
    associated_stream = Streams.TTM
    stream_info = config.StreamInfo.dm02disp
    data_unit = ' mrad'

    plot_length = config.GUI.ttm_plot_length * 1000

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi(ui_path / 'ui/tiptilt.ui', self)
        self.resize(600, 400)

        MinMaxMixin.__init__(self)

        pen = QPen(Color.RED, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.tip = QtCharts.QLineSeries()
        self.tip.setPen(pen)

        pen = QPen(Color.BLUE, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.tilt = QtCharts.QLineSeries()
        self.tilt.setPen(pen)

        # Create Chart and set General Chart setting
        chart = self.tiptilt_plot.chart
        chart.addSeries(self.tip)
        chart.addSeries(self.tilt)

        # X Axis Settings
        self.axisX = QtCharts.QDateTimeAxis()
        self.axisX.setTickCount(5)
        self.axisX.setFormat("HH:mm")
        chart.addAxis(self.axisX, Qt.AlignBottom)
        self.tip.attachAxis(self.axisX)
        self.tilt.attachAxis(self.axisX)

        # Y Axis Settings
        self.axisY = QtCharts.QValueAxis()
        self.axisY.setTickCount(3)
        chart.addAxis(self.axisY, Qt.AlignLeft)
        self.tip.attachAxis(self.axisY)
        self.tilt.attachAxis(self.axisY)

        chart.legend().hide()

        backend.updated.connect(self.update_data)

    def update_data(self):
        timestamp = QDateTime(datetime.now()).toMSecsSinceEpoch()
        tip, tilt = self.backend.data['dm02disp']['data'] * self.data_scaling

        self.tip.append(QPointF(timestamp, tip))
        self.tilt.append(QPointF(timestamp, tilt))

        while self.tip.at(0).x() < timestamp - self.plot_length:
            self.tip.remove(0)
            self.tilt.remove(0)

        self.tip_label.updateText(tip=tip, unit=self.data_unit)
        self.tilt_label.updateText(tilt=tilt, unit=self.data_unit)

        self.update_axis()

    def update_axis(self):
        if self.autoscale_checkbox.isChecked():
            y_min = np.inf
            y_max = -np.inf

            for p in self.tip.points():
                y_min = min(y_min, p.y())
                y_max = max(y_max, p.y())

            for p in self.tilt.points():
                y_min = min(y_min, p.y())
                y_max = max(y_max, p.y())

            self.min_spinbox.setValue(y_min)
            self.max_spinbox.setValue(y_max)
        else:
            y_min = self.data_min
            y_max = self.data_max

        x_min = self.tip.at(0).x()
        x_max = self.tip.at(self.tip.count() - 1).x()

        self.axisX.setRange(
            QDateTime.fromMSecsSinceEpoch(int(x_max) - self.plot_length),
            QDateTime.fromMSecsSinceEpoch(int(x_max)))
        self.axisY.setRange(y_min, y_max)

    def change_units(self, state):
        if state == Qt.Checked:
            self.data_unit = ' asec'
            self.data_scaling = config.TTM.plate_scale
        else:
            self.data_unit = ' mrad'
            self.data_scaling = 1

        new_tip = []
        for p in self.tip.points():
            new_tip.append(
                QPointF(p.x(),
                        p.y() * self.data_scaling / self.data_scaling_prev))

        new_tilt = []
        for p in self.tilt.points():
            new_tilt.append(
                QPointF(p.x(),
                        p.y() * self.data_scaling / self.data_scaling_prev))

        self.tip.replace(new_tip)
        self.tilt.replace(new_tilt)

        self.update_spinboxes_unit()


class PlotsWidget(KalAOWidget):
    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi(ui_path / 'ui/plots.ui', self)
        self.resize(600, 400)

        start = kalao_time.get_start_of_night_dt(kalao_time.now())

        self.start_datetimeedit.setDateTime(start)
        self.stop_datetimeedit.setDateTime(start + timedelta(hours=24))


class LogsWidget(KalAOWidget):
    lines = config.GUI.logs_lines

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi(ui_path / 'ui/logs.ui', self)
        self.resize(600, 400)

        self.logs_textedit.document().setDefaultStyleSheet(f"""
            span {{
                white-space: pre;            
            }}
            .bold {{
                font-weight: bold;
            }}
            .red {{
                color: {Color.RED.name()};
            }}
            .yellow {{
                color: {Color.YELLOW.name()};
            }}
            .green {{
                color: {Color.GREEN.name()};
            }}
            .grey {{
                color: {Color.GREY.name()};
            }}
            .blink {{
              animation: blinker 1s linear infinite;
            }}
            @keyframes blinker {{
              50% {{
                opacity: 0;
              }}
            }}
            """)

        self.thread = LogsThread(parent=self)
        self.thread.log.connect(self.update_data)
        self.thread.start()

        self.acknowledge_button.clicked.connect(self.acknowledge_clicked)

    def update_data(self, log):
        if log is None:
            return

        if log['type'] == LogType.ERROR:
            self.errors_spinbox.setValue(self.errors_spinbox.value() + 1)
        elif log['type'] == LogType.WARNING:
            self.warnings_spinbox.setValue(self.warnings_spinbox.value() + 1)

        self.logs_textedit.append(log['text'])

        while self.logs_textedit.document().blockCount() > self.lines:
            cursor = QTextCursor(self.logs_textedit.document().firstBlock())
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

    def acknowledge_clicked(self, checked):
        self.errors_spinbox.setValue(0)
        self.warnings_spinbox.setValue(0)

    def reset_scrollbars(self):
        horizontal_scrollbar = self.logs_textedit.horizontalScrollBar()
        horizontal_scrollbar.setValue(0)

        vertical_scrollbar = self.logs_textedit.verticalScrollBar()
        vertical_scrollbar.setValue(vertical_scrollbar.maximum())

    def resizeEvent(self, event):
        self.reset_scrollbars()

        super().resizeEvent(event)


class UnifiedWindow(KalAOMainWindow):
    previous_update_time = 0

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi(ui_path / 'ui/unified.ui', self)

        #self.showMaximized()

        self.move(100, 0)
        self.resize(1200, 1050)
        self.show()

        self.wfs = WFSWidget(backend, parent=self)
        self.fli = FLIWidget(backend, parent=self)
        self.slopes = SlopesWidget(backend, parent=self)
        self.flux = FluxWidget(backend, parent=self)
        self.dm = DMWidget(backend, parent=self)
        self.ttm = TTMWidget(backend, parent=self)
        self.plots = PlotsWidget(backend, parent=self)
        self.logs = LogsWidget(backend, parent=self)

        self.wfs_frame.layout().addWidget(self.wfs)
        self.fli_frame.layout().addWidget(self.fli)
        self.dm_frame.layout().addWidget(self.dm)
        self.slopes_frame.layout().addWidget(self.slopes)
        self.flux_frame.layout().addWidget(self.flux)
        self.ttm_frame.layout().addWidget(self.ttm)

        self.plots_tab.layout().addWidget(self.plots)

        self.logs_tab.layout().addWidget(self.logs)

        for widget in [self.fli, self.slopes, self.dm, self.ttm]:
            self.onsky_checkbox.stateChanged.connect(widget.change_units)
            widget.change_units(self.onsky_checkbox.checkState())

        for widget in [self.wfs, self.fli, self.slopes, self.flux, self.dm]:
            self.colormap_checkbox.stateChanged.connect(widget.change_colormap)
            widget.change_colormap(self.colormap_checkbox.checkState())

        self.freeze_checkbox.stateChanged.connect(self.freeze_checkbox_changed)

        self.wfs.hovered.connect(self.info_point)
        self.fli.hovered.connect(self.info_point)
        self.slopes.hovered.connect(self.info_point)
        self.flux.hovered.connect(self.info_point)
        self.dm.hovered.connect(self.info_point)

        self.tabwidget.currentChanged.connect(self.tab_changed)
        self.tab_changed(self.tabwidget.currentIndex())

        self.logo_label.load(str(Logo.svg))
        self.logo_label.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        backend.updated.connect(self.update_data)

        checkbox = QCheckBox("DM Loop ON")
        self.statusBar().addPermanentWidget(checkbox)

        checkbox = QCheckBox("TTM Loop ON")
        self.statusBar().addPermanentWidget(checkbox)

        self.fps_label = KalAOLabel("GUI FPS : {fps:.1f}")
        self.statusBar().addPermanentWidget(self.fps_label)

    def freeze_checkbox_changed(self, state):
        if state == Qt.Checked:
            timer_images.stop()
        else:
            timer_images.start()

    def info_point(self, string):
        if string:
            self.statusbar.showMessage(string)
        else:
            self.statusbar.clearMessage()

    def tab_changed(self, i):
        # Main tab
        if i == 0:
            timer_images.start()

        # Plots tab
        elif i == 1:
            pass

        # Logs tab
        elif i == 2:
            self.logs.reset_scrollbars()

        if i != 0:
            timer_images.stop()

    def update_data(self):
        now = time.monotonic()

        self.fps_label.updateText(fps=(1/(now-self.previous_update_time)))

        self.previous_update_time =now



##### Update functions


def clean():
    #if poke_stream is not None:
    print('Resetted DM pattern')
    #toolbox.zero_stream(poke_stream)

    unified.logs.thread.requestInterruption()
    unified.logs.thread.quit()
    unified.logs.thread.wait()


def handler(signal_received, frame):
    app.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='KalAO - Main GUI.')
    parser.add_argument('--split', action="store_true", dest="split",
                        help='Split windows')
    parser.add_argument('--onsky', action="store_true", dest="onsky",
                        help='On sky units')
    parser.add_argument('--max-fps', action="store", dest="fps", default=10,
                        type=int, help='Max FPS')
    parser.add_argument('--simulation', action="store_true", dest="simulation",
                        help='Simulation mode')

    args = parser.parse_args()

    signal(SIGINT, handler)

    # Qt stuff

    loader = QUiLoader()
    loader.registerCustomWidget(KalAOLabel)
    loader.registerCustomWidget(KalAOGraphicsView)
    loader.registerCustomWidget(KalAOChart)
    loader.registerCustomWidget(KalAOSvgWidget)

    app = QApplication(['KalAO - AO tools'])
    app.setQuitOnLastWindowClosed(True)
    app.aboutToQuit.connect(clean)

    if False:
        app.setStyleSheet("""
        * {
        border: 1px solid red !important;
        }
        """)

    # Backend

    if args.simulation:
        backend = SimulationBackend()
        LogsThread = SimulationLogsThread
    else:
        backend = LocalBackend()
        LogsThread = LocalLogsThread

    # Timer

    timer_images = QTimer()
    timer_images.setInterval(int(1000. / args.fps))
    timer_images.timeout.connect(backend.update)
    timer_images.start()

    # TODO
    #timer_tiptilt = QTimer()
    #timer_tiptilt.setInterval(int(1000. / args.fps))
    #timer_tiptilt.timeout.connect(backend.update_tiptilt)
    #timer_tiptilt.start()

    # Windows

    if args.split:
        wfs = WFSWidget(backend)
        wfs.show()

        fli = FLIWidget(backend)
        fli.show()

        slopes = SlopesWidget(backend)
        slopes.show()

        flux = FluxWidget(backend)
        flux.show()

        dm = DMWidget(backend)
        dm.show()

        ttm = TTMWidget(backend)
        ttm.show()

        logs_window = LogsWidget(backend)
        logs_window.show()

        if args.onsky:
            fli.change_units(Qt.Checked)
            slopes.change_units(Qt.Checked)
            dm.change_units(Qt.Checked)
            ttm.change_units(Qt.Checked)

    else:
        unified = UnifiedWindow(backend)

        if args.onsky:
            unified_view.onsky_checkbox.setChecked(True)

    backend.update()

    app.exec_()

    #TODO
    #def closeEvent(self, event):
    #    if self.associated_stream is not None:
    #        stream = streams.get(self.associated_stream)
    #        if stream is not None:
    #            print(f'Closing {self.associated_stream}')
    #            #stream.close()
    #            del streams[self.associated_stream]
    #
    #    event.accept()
