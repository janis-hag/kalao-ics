from typing import Any

import numpy as np

from PySide6.QtCharts import QDateTimeAxis, QLineSeries, QValueAxis
from PySide6.QtCore import QDateTime, QPointF, QSignalBlocker, Signal
from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import QWidget

from compiled.ui_ttm import Ui_TTMWidget

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin, MinMaxMixin
from kalao.guis.utils.widgets import KWidget

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

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend

        self.ui = Ui_TTMWidget()
        self.ui.setupUi(self)

        self.resize(600, 400)

        self.init_minmax(self.ui.tiptilt_plot)

        chart = self.ui.tiptilt_plot.chart()
        chart.legend().hide()

        self.tip_points = []
        self.tilt_points = []

        pen = QPen(Color.RED, 1, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)

        tip_series = self.tip_series = QLineSeries()
        tip_series.setUseOpenGL(True)
        tip_series.setPen(pen)
        tip_series.setName('Tip')
        chart.addSeries(tip_series)

        if config.GUI.opengl_charts:
            tip_series.setUseOpenGL(True)

        pen = QPen(Color.BLUE, 1, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)

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
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        tip_series.attachAxis(axis_x)
        tilt_series.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.axis_y = QValueAxis()
        axis_y.setTickCount(5)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        tip_series.attachAxis(axis_y)
        tilt_series.attachAxis(axis_y)

        chart.hovered.connect(self.hover_xy_to_str)

        self.update_labels()

        backend.all_updated.connect(self.all_updated)

    def all_updated(self, data: dict[str, Any]) -> None:
        img = self.consume_shm(data, config.SHM.TTM, force=True)

        if img is not None:
            timestamp_msec = int(
                self.consume_metadata(data, 'timestamp') * 1000)
            self.tip, self.tilt = img

            saturation_tip = max(self.tip / self.image_info['max'],
                                 self.tip / self.image_info['min'])
            saturation_tilt = max(self.tip / self.image_info['max'],
                                  self.tilt / self.image_info['min'])
            self.saturation = max(saturation_tip, saturation_tilt)

            # Add new point

            self.tip_points.append(
                QPointF(timestamp_msec, self.tip * self.data_scaling))
            self.tilt_points.append(
                QPointF(timestamp_msec, self.tilt * self.data_scaling))

            # Delete old points

            while self.tip_points[0].x() < timestamp_msec - self.plot_length:
                del self.tip_points[0]
                del self.tilt_points[0]

            # Update plots

            self.tip_series.replace(self.tip_points)
            self.tilt_series.replace(self.tilt_points)

            self.update_labels()
            self.update_axis()

    def update_labels(self) -> None:
        self.ui.tip_label.updateText(tip=self.tip * self.data_scaling,
                                     unit=self.data_unit)
        self.ui.tilt_label.updateText(tilt=self.tilt * self.data_scaling,
                                      unit=self.data_unit)

        if self.saturation >= 1:
            self.ui.saturation_label.setText('Saturated !')
            self.ui.saturation_label.setStyleSheet(
                f'color: {Color.RED.name()};')
        else:
            self.ui.saturation_label.updateText(saturation=self.saturation *
                                                100)
            self.ui.saturation_label.setStyleSheet('')

    def update_axis(self) -> None:
        y_min = np.inf
        y_max = -np.inf

        for p in self.tip_points:
            y_min = min(y_min, p.y())
            y_max = max(y_max, p.y())

        for p in self.tilt_points:
            y_min = min(y_min, p.y())
            y_max = max(y_max, p.y())

        self.autoscale_min = y_min
        self.autoscale_max = y_max

        if self.ui.autoscale_button.isChecked():
            with QSignalBlocker(self.ui.min_spinbox):
                self.ui.min_spinbox.setMaximum(y_max / self.data_scaling)
                self.ui.min_spinbox.setValue(y_min / self.data_scaling)

            with QSignalBlocker(self.ui.max_spinbox):
                self.ui.max_spinbox.setMinimum(y_min / self.data_scaling)
                self.ui.max_spinbox.setValue(y_max / self.data_scaling)
        else:
            y_min = self.ui.min_spinbox.value() * self.data_scaling
            y_max = self.ui.max_spinbox.value() * self.data_scaling

        delta = y_max - y_min
        if abs(delta) < config.epsilon:
            y_min -= 0.01
            y_max += 0.01
        else:
            y_min -= 0.05 * delta
            y_max += 0.05 * delta

        if len(self.tip_points) == 0:
            return

        x_max = QDateTime.currentDateTime()
        x_min = x_max.addSecs(-config.GUI.ttm_plot_length)

        self.axis_x.setRange(x_min, x_max)
        self.axis_y.setRange(y_min, y_max)

    def change_units(self, state: Qt.CheckState) -> None:
        prev_scaling = self.data_scaling
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.update_spinboxes_unit('"', config.TTM.plate_scale, 2)
        else:
            self.update_spinboxes_unit(' mrad', 1, 2)

        self.update_labels()

        new_tip = []
        for p in self.tip_points:
            new_tip.append(
                QPointF(p.x(),
                        p.y() * self.data_scaling / prev_scaling))
        self.tip_points = new_tip

        new_tilt = []
        for p in self.tilt_points:
            new_tilt.append(
                QPointF(p.x(),
                        p.y() * self.data_scaling / prev_scaling))
        self.tilt_points = new_tilt

        self.tip_series.replace(self.tip_points)
        self.tilt_series.replace(self.tilt_points)

        self.update_axis()

    def hover_xy_to_str(self, series: QLineSeries, x: float, y: float) -> None:
        if not np.isnan(x) and not np.isnan(y):
            x = QDateTime.fromMSecsSinceEpoch(
                int(x)).toString('HH:mm:ss dd-MM-yy')

            self.hovered.emit(f'{y:.{self.data_precision}f} at {x}')
        else:
            self.hovered.emit('')
