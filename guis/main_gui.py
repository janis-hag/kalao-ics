import argparse
import time
from datetime import datetime
from pathlib import Path
from signal import SIGINT, signal

import numpy as np

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QDateTime, QPoint, QPointF, QTimer
from PySide2.QtGui import QFont, QPen, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QApplication, QCheckBox, QGraphicsItem,
                               QMainWindow, QToolTip)

from kalao.cacao import toolbox
from kalao.interfaces import fake_data
from kalao.utils import kalao_tools

from guis.lib import colormaps
from guis.lib.kalao_widgets import (Color, HoverMixin, KalAOChart,
                                    KalAOGraphicsView, KalAOLabel, KalAOWidget,
                                    MinMaxMixin, OffsetedTextItem)
from guis.lib.ui_loader import loadUi

import config

Streams = config.Streams

streams = {}

ui_path = Path(__file__).absolute().parent


def global_key_press(event):
    if event.key() == Qt.Key_Q or event.key() == Qt.Key_X or event.key(
    ) == Qt.Key_Escape:
        app.quit()


class WFSWindow(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = Streams.NUVU
    stream_info = config.StreamInfo.nuvu_stream
    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi(ui_path / 'ui/wfs.ui', self)

        MinMaxMixin.__init__(self)

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

        self.wfs_view.scene.hovered.connect(self.hover_event)

    def update_data(self, img):
        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.img = img

        self.wfs_view.setImage(img, img_min, img_max)

    def keyPressEvent(self, event):
        global_key_press(event)

        super().keyPressEvent(event)

    subap_current = None

    def hover_event(self, x, y, screenPos):
        #self.tooltip= QToolTip()

        pen = QPen(Color.GREEN, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        img = self.img

        if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
            string = f'X: {(x-self.data_center_x)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, Y: {(y-self.data_center_y)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, V: {img[y,x]:.{self.data_precision}f}{self.data_unit}'

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
                self.tooltip.hideText()

            self.hovered.emit(string)
        else:
            self.reset_subap_color()
            self.tooltip.hideText()

            self.hovered.emit('')

    def reset_subap_color(self):
        if self.subap_current is not None:
            self.rois[self.subap_current].setPen(self.subap_previous_pen)

            self.subap_current = None
            self.subap_previous_pen = None


class FLIWindow(KalAOWidget, MinMaxMixin, HoverMixin):
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

    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi(ui_path / 'ui/fli.ui', self)

        MinMaxMixin.__init__(self)

        pen = QPen(Color.BLUE, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.data_center_x = config.FLI.center_x
        self.data_center_y = config.FLI.center_y
        self.WFS_fov = 4 * config.WFS.plate_scale / config.FLI.plate_scale

        self.roi = self.fli_view.scene.addEllipse(
            self.data_center_x - self.WFS_fov / 2, self.data_center_y -
            self.WFS_fov / 2, self.WFS_fov, self.WFS_fov, pen)
        self.roi.setZValue(1)

        #self.ticks_pos = [384, 256, 128, 0, -128, -256, -384]
        self.ticks_pos = [-400, -300, -200, -100, 0, 100, 200, 300, 400]
        self.addTicks()

        self.fli_view.scene.hovered.connect(self.hover_event)

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

    def update_data(self, img):
        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.img = img

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

    def keyPressEvent(self, event):
        global_key_press(event)

        super().keyPressEvent(event)


class SlopesWindow(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = Streams.SLOPES
    stream_info = config.StreamInfo.shwfs_slopes
    data_unit = ' px'
    data_precision = 3

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi(ui_path / 'ui/slopes.ui', self)

        MinMaxMixin.__init__(self)

        self.slopes_view.colormap = colormaps.BWR()

        self.slopes_view.scene.hovered.connect(self.hover_event)

    def update_data(self, img, tip, tilt, residual):
        img *= self.data_scaling
        tip *= self.data_scaling
        tilt *= self.data_scaling
        residual *= self.data_scaling

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

        self.img = img

        self.slopes_view.setImage(img, img_min, img_max)

        self.tip_label.updateText(tip=tip, unit=self.data_unit)
        self.tilt_label.updateText(tilt=tilt, unit=self.data_unit)
        self.residual_label.updateText(residual=residual, unit=self.data_unit)

    def keyPressEvent(self, event):
        global_key_press(event)

        super().keyPressEvent(event)

    def change_units(self, state):
        if state == Qt.Checked:
            self.data_unit = ' asec'
            self.data_scaling = config.WFS.plate_scale
        else:
            self.data_unit = ' px'
            self.data_scaling = 1

        self.update_spinboxes_unit()


class FluxWindow(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = Streams.FLUX
    stream_info = config.StreamInfo.shwfs_slopes_flux
    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi(ui_path / 'ui/flux.ui', self)

        MinMaxMixin.__init__(self)

        self.flux_view.scene.hovered.connect(self.hover_event)

    def update_data(self, img, flux_avg, flux_brightest):
        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.img = img

        self.flux_view.setImage(img, img_min, img_max)

        self.flux_avg_label.updateText(flux_avg=flux_avg, unit=self.data_unit)
        self.flux_brightest_label.updateText(flux_brightest=flux_brightest,
                                             unit=self.data_unit)

    def keyPressEvent(self, event):
        global_key_press(event)

        super().keyPressEvent(event)


class DMWindow(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = Streams.DM
    stream_info = config.StreamInfo.dm01disp
    data_unit = ' um'
    data_precision = 3

    axis_unit = ' px'
    axis_precision = 0

    #TODO: modify stream_info with stroke_max?

    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi(ui_path / 'ui/dm.ui', self)

        MinMaxMixin.__init__(self)

        self.dm_view.colormap = colormaps.BWR()

        self.dm_view.scene.hovered.connect(self.hover_event)

    def update_data(self, img, max_stroke):
        img *= self.data_scaling
        max_stroke *= self.data_scaling

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

        self.img = img

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

    def keyPressEvent(self, event):
        global_key_press(event)

        super().keyPressEvent(event)


class TTMWindow(KalAOWidget, MinMaxMixin):
    associated_stream = Streams.TTM
    stream_info = config.StreamInfo.dm02disp
    data_unit = ' mrad'

    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi(ui_path / 'ui/tiptilt.ui', self)

        MinMaxMixin.__init__(self)

        self.time_length = 5 * 60 * 1000

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
        chart.addAxis(self.axisY, Qt.AlignLeft)
        self.tip.attachAxis(self.axisY)
        self.tilt.attachAxis(self.axisY)

        chart.legend().hide()

    def update_data(self, tiptilt):
        timestamp = QDateTime(datetime.now()).toMSecsSinceEpoch()
        tip, tilt = tiptilt * self.data_scaling

        self.tip.append(QPointF(timestamp, tip))
        self.tilt.append(QPointF(timestamp, tilt))

        while self.tip.at(0).x() < timestamp - self.time_length:
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

        ttm.axisX.setRange(
            QDateTime.fromMSecsSinceEpoch(int(x_max) - self.time_length),
            QDateTime.fromMSecsSinceEpoch(int(x_max)))
        ttm.axisY.setRange(y_min, y_max)

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

    def keyPressEvent(self, event):
        global_key_press(event)

        super().keyPressEvent(event)


class UnifiedWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        loadUi(ui_path / 'ui/unified.ui', self)

        #self.showMaximized()

        self.move(100, 0)
        self.resize(1200, 1050)
        self.show()

        self.wfs = WFSWindow()
        self.fli = FLIWindow()
        self.slopes = SlopesWindow()
        self.flux = FluxWindow()
        self.dm = DMWindow()
        self.ttm = TTMWindow()

        self.wfs_frame.layout().addWidget(self.wfs, 0, 0)
        self.fli_frame.layout().addWidget(self.fli, 0, 0)

        self.dm_frame.layout().addWidget(self.dm, 0, 0)
        self.slopes_frame.layout().addWidget(self.slopes, 0, 0)
        self.flux_frame.layout().addWidget(self.flux, 0, 0)
        self.ttm_frame.layout().addWidget(self.ttm, 0, 0)

        self.onsky_checkbox.stateChanged.connect(self.fli.change_units)
        self.onsky_checkbox.stateChanged.connect(self.slopes.change_units)
        self.onsky_checkbox.stateChanged.connect(self.dm.change_units)
        self.onsky_checkbox.stateChanged.connect(self.ttm.change_units)

        self.freeze_checkbox.stateChanged.connect(self.freeze_checkbox_changed)

        self.wfs.hovered.connect(self.info_point)
        self.fli.hovered.connect(self.info_point)
        self.slopes.hovered.connect(self.info_point)
        self.flux.hovered.connect(self.info_point)
        self.dm.hovered.connect(self.info_point)

        checkbox = QCheckBox("DM Loop ON")
        self.statusBar().addPermanentWidget(checkbox)

        checkbox = QCheckBox("TTM Loop ON")
        self.statusBar().addPermanentWidget(checkbox)

    def freeze_checkbox_changed(self, state):
        if state == Qt.Checked:
            timer.stop()
        else:
            timer.start()

    def info_point(self, string):
        if string:
            self.statusbar.showMessage(string)
        else:
            self.statusbar.clearMessage()


##### Update functions

previous = 0


def update_display():
    global previous

    now = time.monotonic()

    if Streams.NUVU in streams:
        data_nuvu = nuvu_stream.get_data(check=False)
        wfs.update_data(data_nuvu)

    if Streams.FLI in streams:
        data_fli = fli_stream.get_data(check=False)
        fli.update_data(data_fli)

    if Streams.SLOPES in streams:
        data_slopes = slopes_stream.get_data(check=False)
        tip = slopes_fps.get_param('slope_x')
        tilt = slopes_fps.get_param('slope_y')
        residual = slopes_fps.get_param('residual')
        slopes.update_data(data_slopes, tip, tilt, residual)

    if Streams.FLUX in streams:
        data_flux = flux_stream.get_data(check=False)
        flux_avg = slopes_fps.get_param('flux_subaperture_avg')
        flux_brightest = slopes_fps.get_param('flux_subaperture_brightest')
        flux.update_data(data_flux, flux_avg, flux_brightest)

    if Streams.DM in streams:
        data_dm = dm_stream.get_data(check=False)
        max_stroke = bmc_fps.get_param('max_stroke')
        dm.update_data(data_dm, max_stroke)

    if Streams.TTM in streams:
        data_ttm = ttm_stream.get_data(check=False)
        ttm.update_data(data_ttm)

    #if w is not None:
    #    w.update_data(1/(now - previous))

    previous = now


ttm_data = np.array([0, 0])


def update_fake():
    global ttm_data

    dm_data = fake_data.dm()
    max_stroke = 0.9

    ttm_data = fake_data.tiptilt(seed=ttm_data)

    nuvu_data = fake_data.nuvu_frame(tiptilt=ttm_data,
                                     dmdisp=np.ma.getdata(dm_data))

    fli_data = fake_data.fli_frame(tiptilt=ttm_data,
                                   dmdisp=np.ma.getdata(dm_data))

    slopes_data = fake_data.slopes(nuvu_data)
    slopes_params = fake_data.slopes_params(slopes_data)

    flux_data = fake_data.flux(nuvu_data)
    flux_params = fake_data.flux_params(flux_data)

    wfs.update_data(nuvu_data)
    fli.update_data(fli_data)
    slopes.update_data(slopes_data.filled(), slopes_params['tip'],
                       slopes_params['tilt'], slopes_params['residual'])
    flux.update_data(flux_data.filled(), flux_params['flux_subaperture_avg'],
                     flux_params['flux_subaperture_brightest'])
    dm.update_data(dm_data.filled(), max_stroke)
    ttm.update_data(ttm_data)


def clean():
    #if poke_stream is not None:
    print('Resetted DM pattern')
    #toolbox.zero_stream(poke_stream)


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
    parser.add_argument('--test', action="store_true", dest="test",
                        help='Test')

    args = parser.parse_args()

    signal(SIGINT, handler)

    ##### Qt stuff

    loader = QUiLoader()
    loader.registerCustomWidget(KalAOLabel)
    loader.registerCustomWidget(KalAOGraphicsView)
    loader.registerCustomWidget(KalAOChart)

    app = QApplication(['KalAO - AO tools'])
    app.setQuitOnLastWindowClosed(True)
    app.aboutToQuit.connect(clean)

    if False:
        app.setStyleSheet("""
        * {
        border: 1px solid red !important;
        }
        """)

    ##### Open needed streams

    if not args.test:
        nuvu_stream = toolbox.open_stream_once(Streams.NUVU, streams)
        poke_stream = toolbox.open_stream_once("dm01disp09", streams)
        dm_stream = toolbox.open_stream_once(Streams.DM, streams)
        ttm_stream = toolbox.open_stream_once(Streams.TTM, streams)
        slopes_stream = toolbox.open_stream_once(Streams.SLOPES, streams)
        flux_stream = toolbox.open_stream_once(Streams.FLUX, streams)
        fli_stream = toolbox.open_stream_once(Streams.FLI, streams)

        slopes_fps = toolbox.open_fps_once('shwfs_process-1', streams)
        nuvu_fps = toolbox.open_fps_once('nuvu_acquire-1', streams)
        bmc_fps = toolbox.open_fps_once('bmc_display-1', streams)

    ##### Windows

    update_fun = update_display

    if args.split:
        if Streams.NUVU in streams or args.test:
            wfs = WFSWindow()
            wfs.show()

        if Streams.FLI in streams or args.test:
            fli = FLIWindow()
            fli.show()

        if Streams.SLOPES in streams or args.test:
            slopes = SlopesWindow()
            slopes.show()

        if Streams.FLUX in streams or args.test:
            flux = FluxWindow()
            flux.show()

        if Streams.DM in streams or args.test:
            dm = DMWindow()
            dm.show()

        if Streams.TTM in streams or args.test:
            ttm = TTMWindow()
            ttm.show()

        if args.onsky:
            fli.change_units(Qt.Checked)
            slopes.change_units(Qt.Checked)
            dm.change_units(Qt.Checked)
            ttm.change_units(Qt.Checked)

    else:
        unified = UnifiedWindow()

        wfs = unified.wfs
        fli = unified.fli
        slopes = unified.slopes
        flux = unified.flux
        dm = unified.dm
        ttm = unified.ttm

        if args.onsky:
            unified_view.onsky_checkbox.setChecked(True)

    if args.test:
        update_fun = update_fake

    update_fun()

    # Timing - monitor fps and trigger refresh
    timer = QTimer()
    timer.setInterval(int(1000. / args.fps))
    timer.timeout.connect(update_fun)
    timer.start()

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
