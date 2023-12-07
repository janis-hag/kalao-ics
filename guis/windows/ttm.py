from datetime import datetime

import numpy as np

from PySide6.QtCharts import QDateTimeAxis, QLineSeries, QValueAxis
from PySide6.QtCore import QDateTime, QPointF
from PySide6.QtGui import QPen, Qt

from guis.kalao.definitions import Color
from guis.kalao.mixins import MinMaxMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

import config


class TTMWidget(KalAOWidget, MinMaxMixin):
    associated_stream = config.Streams.TTM
    stream_info = config.StreamInfo.dm02disp
    data_unit = ' mrad'

    plot_length = config.GUI.ttm_plot_length * 1000

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('ttm.ui', self)
        self.resize(600, 400)

        MinMaxMixin.init(self)

        pen = QPen(Color.RED, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.tip = QLineSeries()
        self.tip.setPen(pen)
        self.tip.setName('Tip')

        pen = QPen(Color.BLUE, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.tilt = QLineSeries()
        self.tilt.setPen(pen)
        self.tilt.setName('Tilt')

        # Create Chart and set General Chart setting
        chart = self.tiptilt_plot.chart
        chart.addSeries(self.tip)
        chart.addSeries(self.tilt)

        # X Axis Settings
        self.axisX = QDateTimeAxis()
        self.axisX.setTickCount(5)
        self.axisX.setFormat("HH:mm")
        chart.addAxis(self.axisX, Qt.AlignBottom)
        self.tip.attachAxis(self.axisX)
        self.tilt.attachAxis(self.axisX)

        # Y Axis Settings
        self.axisY = QValueAxis()
        self.axisY.setTickCount(3)
        chart.addAxis(self.axisY, Qt.AlignLeft)
        self.tip.attachAxis(self.axisY)
        self.tilt.attachAxis(self.axisY)

        chart.legend().hide()

        self.tip_label.updateText(tip=np.nan, unit=self.data_unit)
        self.tilt_label.updateText(tilt=np.nan, unit=self.data_unit)

        backend.data_updated.connect(self.data_updated)

    def data_updated(self, data):
        img = self.backend.consume_stream(data, config.Streams.TTM)

        if img is not None:
            timestamp = QDateTime(datetime.now()).toMSecsSinceEpoch()
            tip, tilt = img * self.data_scaling

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

        if abs(y_max - y_min) < config.epsilon:
            y_min -= 0.01
            y_max += 0.01

        x_max = self.tip.at(self.tip.count() - 1).x()

        self.axisX.setRange(
            QDateTime.fromMSecsSinceEpoch(int(x_max) - self.plot_length),
            QDateTime.fromMSecsSinceEpoch(int(x_max)))
        self.axisY.setRange(y_min, y_max)

    def change_units(self, state):
        if Qt.CheckState(state) == Qt.Checked:
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
