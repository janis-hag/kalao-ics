from datetime import datetime

import numpy as np

from PySide6.QtCharts import QDateTimeAxis, QLineSeries, QValueAxis
from PySide6.QtCore import QDateTime, QPointF, QSignalBlocker
from PySide6.QtGui import QPen, Qt

from guis.kalao.definitions import Color
from guis.kalao.mixins import BackendDataMixin, MinMaxMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

import config


class TTMWidget(KalAOWidget, MinMaxMixin, BackendDataMixin):
    associated_stream = config.Streams.TTM
    stream_info = config.StreamInfo.dm02disp

    data_unit = ' mrad'

    plot_length = config.GUI.ttm_plot_length * 1000

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('ttm.ui', self)
        self.resize(600, 400)

        self.init_minmax(self.tiptilt_plot)

        chart = self.tiptilt_plot.chart

        pen = QPen(Color.RED, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        tip_series = self.tip_series = QLineSeries()
        tip_series.setPen(pen)
        tip_series.setName('Tip')
        chart.addSeries(tip_series)

        pen = QPen(Color.BLUE, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        tilt_series = self.tilt_series = QLineSeries()
        tilt_series.setPen(pen)
        tilt_series.setName('Tilt')
        chart.addSeries(tilt_series)

        # X Axis Settings
        axis_x = self.axis_x = QDateTimeAxis()
        axis_x.setTickCount(5)
        axis_x.setFormat("HH:mm")
        chart.addAxis(axis_x, Qt.AlignBottom)
        tip_series.attachAxis(axis_x)
        tilt_series.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.axis_y = QValueAxis()
        axis_y.setTickCount(3)
        chart.addAxis(axis_y, Qt.AlignLeft)
        tip_series.attachAxis(axis_y)
        tilt_series.attachAxis(axis_y)

        chart.legend().hide()

        self.tip_label.updateText(tip=np.nan, unit=self.data_unit)
        self.tilt_label.updateText(tilt=np.nan, unit=self.data_unit)

        backend.data_updated.connect(self.data_updated)

    def data_updated(self, data):
        img = self.consume_stream(data, config.Streams.TTM)

        if img is not None:
            timestamp = QDateTime(datetime.now()).toMSecsSinceEpoch()
            tip, tilt = img * self.data_scaling

            self.tip_series.append(QPointF(timestamp, tip))
            self.tilt_series.append(QPointF(timestamp, tilt))

            while self.tip_series.at(0).x() < timestamp - self.plot_length:
                self.tip_series.remove(0)
                self.tilt_series.remove(0)

            self.tip_label.updateText(tip=tip, unit=self.data_unit)
            self.tilt_label.updateText(tilt=tilt, unit=self.data_unit)

            self.update_axis()

    def update_axis(self):
        if self.autoscale_checkbox.isChecked():
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

            with QSignalBlocker(self.min_spinbox):
                self.min_spinbox.setMaximum(y_max / self.data_scaling)
                self.min_spinbox.setValue(y_min / self.data_scaling)

            with QSignalBlocker(self.max_spinbox):
                self.max_spinbox.setMinimum(y_min / self.data_scaling)
                self.max_spinbox.setValue(y_max / self.data_scaling)
        else:
            y_min = self.min_spinbox.value() * self.data_scaling
            y_max = self.max_spinbox.value() * self.data_scaling

        if abs(y_max - y_min) < config.epsilon:
            y_min -= 0.01
            y_max += 0.01

        if self.tip_series.count() == 0:
            return

        x_max = self.tip_series.at(self.tip_series.count() - 1).x()

        self.axis_x.setRange(
            QDateTime.fromMSecsSinceEpoch(int(x_max) - self.plot_length),
            QDateTime.fromMSecsSinceEpoch(int(x_max)))
        self.axis_y.setRange(y_min, y_max)

    def change_units(self, state):
        prev_scaling = self.data_scaling
        if Qt.CheckState(state) == Qt.Checked:
            self.update_spinboxes_unit(' asec', config.TTM.plate_scale)
        else:
            self.update_spinboxes_unit(' mrad', 1)

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
