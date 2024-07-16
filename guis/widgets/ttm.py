import math
from datetime import timezone

import numpy as np

from PySide6.QtCharts import QDateTimeAxis, QLineSeries, QValueAxis
from PySide6.QtCore import (QDateTime, QPointF, QSignalBlocker, QTimeZone,
                            Signal)
from PySide6.QtGui import QPen, Qt

from guis.utils.definitions import Color
from guis.utils.mixins import BackendDataMixin, MinMaxMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KWidget

import config


class TTMWidget(KWidget, MinMaxMixin, BackendDataMixin):
    image_info = config.Images.dm02disp

    hovered = Signal(str)

    data_unit = ' mrad'
    data_precision = 2

    plot_length = config.GUI.ttm_plot_length * 1000

    saturation = np.nan
    tip = np.nan
    tilt = np.nan

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('ttm.ui', self)
        self.resize(600, 400)

        self.init_minmax(self.tiptilt_plot)

        chart = self.tiptilt_plot.chart()

        pen = QPen(Color.RED, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)

        tip_series = self.tip_series = QLineSeries()
        tip_series.setUseOpenGL(True)
        tip_series.setPen(pen)
        tip_series.setName('Tip')
        chart.addSeries(tip_series)

        if config.GUI.opengl_charts:
            tip_series.setUseOpenGL(True)

        pen = QPen(Color.BLUE, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)

        tilt_series = self.tilt_series = QLineSeries()
        tilt_series.setPen(pen)
        tilt_series.setName('Tilt')
        chart.addSeries(tilt_series)

        if config.GUI.opengl_charts:
            tilt_series.setUseOpenGL(True)

        # X Axis Settings
        axis_x = self.axis_x = QDateTimeAxis()
        axis_x.setTickCount(5)
        axis_x.setFormat('H:mm:ss')
        chart.addAxis(axis_x, Qt.AlignBottom)
        tip_series.attachAxis(axis_x)
        tilt_series.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.axis_y = QValueAxis()
        axis_y.setTickCount(5)
        chart.addAxis(axis_y, Qt.AlignLeft)
        tip_series.attachAxis(axis_y)
        tilt_series.attachAxis(axis_y)

        chart.legend().hide()

        chart.hovered.connect(self.hover_xy_to_str)

        self.update_labels()

        backend.all_updated.connect(self.all_updated)

    def all_updated(self, data):
        img = self.consume_shm(data, config.SHM.TTM)

        if img is not None:
            timestamp_msec = int(
                self.consume_metadata(data, 'timestamp').timestamp() * 1000)
            self.tip, self.tilt = img

            saturation_tip = max(self.tip / self.image_info['max'],
                                 self.tip / self.image_info['min'])
            saturation_tilt = max(self.tip / self.image_info['max'],
                                  self.tilt / self.image_info['min'])
            self.saturation = max(saturation_tip, saturation_tilt)

            self.tip_series.append(
                QPointF(timestamp_msec, self.tip * self.data_scaling))
            self.tilt_series.append(
                QPointF(timestamp_msec, self.tilt * self.data_scaling))

            while self.tip_series.at(
                    0).x() < timestamp_msec - self.plot_length:
                self.tip_series.remove(0)
                self.tilt_series.remove(0)

            self.update_labels()
            self.update_axis()

    def update_labels(self):
        self.tip_label.updateText(tip=self.tip * self.data_scaling,
                                  unit=self.data_unit)
        self.tilt_label.updateText(tilt=self.tilt * self.data_scaling,
                                   unit=self.data_unit)

        if self.saturation >= 1:
            self.saturation_label.setText('Saturated !')
            self.saturation_label.setStyleSheet(f'color: {Color.RED.name()};')
        else:
            self.saturation_label.updateText(saturation=self.saturation * 100)
            self.saturation_label.setStyleSheet('')

    def update_axis(self):
        y_min = np.inf
        y_max = -np.inf

        for p in self.tip_series.points():
            y_min = min(y_min, p.y())
            y_max = max(y_max, p.y())

        for p in self.tilt_series.points():
            y_min = min(y_min, p.y())
            y_max = max(y_max, p.y())

        self.autoscale_min = y_min
        self.autoscale_max = y_max

        if self.autoscale_button.isChecked():
            with QSignalBlocker(self.min_spinbox):
                self.min_spinbox.setMaximum(y_max / self.data_scaling)
                self.min_spinbox.setValue(y_min / self.data_scaling)

            with QSignalBlocker(self.max_spinbox):
                self.max_spinbox.setMinimum(y_min / self.data_scaling)
                self.max_spinbox.setValue(y_max / self.data_scaling)
        else:
            y_min = self.min_spinbox.value() * self.data_scaling
            y_max = self.max_spinbox.value() * self.data_scaling

        if math.isclose(y_min, y_max):
            y_min -= 0.01
            y_max += 0.01

        if self.tip_series.count() == 0:
            return

        x_max = QDateTime.currentDateTime()
        x_min = x_max.addSecs(-config.GUI.ttm_plot_length)

        self.axis_x.setRange(x_min, x_max)
        self.axis_y.setRange(y_min, y_max)

    def change_units(self, state):
        prev_scaling = self.data_scaling
        if Qt.CheckState(state) == Qt.Checked:
            self.update_spinboxes_unit('"', config.TTM.plate_scale, 2)
        else:
            self.update_spinboxes_unit(' mrad', 1, 2)

        self.update_labels()

        new_tip = []
        for p in self.tip_series.points():
            new_tip.append(
                QPointF(p.x(),
                        p.y() * self.data_scaling / prev_scaling))

        new_tilt = []
        for p in self.tilt_series.points():
            new_tilt.append(
                QPointF(p.x(),
                        p.y() * self.data_scaling / prev_scaling))

        self.tip_series.replace(new_tip)
        self.tilt_series.replace(new_tilt)

        self.update_axis()

    def hover_xy_to_str(self, series, x, y):
        if not np.isnan(x) and not np.isnan(y):
            x = QDateTime.fromMSecsSinceEpoch(
                int(x)).toString("HH:mm:ss dd-MM-yy")

            self.hovered.emit(f'{y:.{self.data_precision}f} at {x}')
        else:
            self.hovered.emit('')
