import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import scipy.signal

from PySide6.QtCharts import (QDateTimeAxis, QLineSeries, QLogValueAxis,
                              QValueAxis)
from PySide6.QtCore import QDateTime, QPointF, Signal, Slot
from PySide6.QtGui import QColor, QPen, Qt
from PySide6.QtWidgets import QWidget

from compiled.ui_telemetry import Ui_TelemetryWidget

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendActionMixin, BackendDataMixin
from kalao.guis.utils.widgets import KWidget

import config


@dataclass
class TelemetryChart:
    name: str
    unit: str
    precision: int

    chart = None


@dataclass
class TelemetrySeries:
    name: str
    chart_name: str
    color: QColor
    scaling: float
    spectrum: bool = False

    mean_points: list = None
    mean_series: QLineSeries = None

    std_points: list = None
    std_series: QLineSeries = None

    spectrum_points: list = None
    spectrum_series: QLineSeries = None
    spectrum_max: float = 0


class TelemetryWidget(KWidget, BackendActionMixin, BackendDataMixin):
    hovered = Signal(str)

    charts = [
        TelemetryChart(name='ttm', unit='"', precision=2),
        TelemetryChart(name='flux', unit='ADU', precision=0),
        TelemetryChart(name='slopes', unit='"', precision=2),
    ]

    series = [
        TelemetrySeries(name='tip', chart_name='ttm', color=Color.BLUE,
                        scaling=config.TTM.plate_scale, spectrum=True),
        TelemetrySeries(name='tilt', chart_name='ttm', color=Color.RED,
                        scaling=config.TTM.plate_scale, spectrum=True),
        TelemetrySeries(name='flux_avg', chart_name='flux', color=Color.ORANGE,
                        scaling=1),
        TelemetrySeries(name='flux_max', chart_name='flux', color=Color.YELLOW,
                        scaling=1),
        TelemetrySeries(name='residual_rms', chart_name='slopes',
                        color=Color.GREEN, scaling=config.WFS.plate_scale),
        TelemetrySeries(name='slope_x_avg', chart_name='slopes',
                        color=Color.PURPLE, scaling=config.WFS.plate_scale,
                        spectrum=True),
        TelemetrySeries(name='slope_y_avg', chart_name='slopes',
                        color=Color.DARK_BLUE, scaling=config.WFS.plate_scale,
                        spectrum=True),
    ]

    last_timestamp = datetime.fromtimestamp(0)
    df_buffer = None

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend

        self.ui = Ui_TelemetryWidget()
        self.ui.setupUi(self)

        self.resize(600, 400)

        ##### Spectrums

        # Create Chart and set General Chart setting
        chart = self.ui.spectrums_plot.chart()
        chart.legend().hide()

        # X Axis Settings
        axis_x = self.spectrums_axis_x = QLogValueAxis()
        axis_x.setBase(10)
        axis_x.setRange(0.1, 1000)
        axis_x.setMinorTickCount(8)
        axis_x.setTitleText('Frequency [Hz]')
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)

        # Y Axis Settings
        axis_y = self.spectrums_axis_y = QValueAxis()
        axis_y.setTickCount(7)
        axis_y.setRange(-0.05, 1.05)
        axis_y.setTitleText('Amplitude RMS')
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

        chart.hovered.connect(self.hover_xy_to_str_spectrum)

        self.spectrum_key_list = []

        for series in self.series:
            if not series.spectrum:
                continue

            self.spectrum_key_list.append(series.name)

            getattr(self.ui, f'{series.name}_spectrum_checkbox').setStyleSheet(
                f'color: {series.color.name()}')

            pen = QPen(series.color, 1.25, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)

            series_spectrum = QLineSeries()
            series_spectrum.setPen(pen)
            series_spectrum.setName(f'{series.name} spectrum')
            chart.addSeries(series_spectrum)
            series_spectrum.attachAxis(axis_x)
            series_spectrum.attachAxis(axis_y)

            series.spectrum_points = []
            series.spectrum_series = series_spectrum

            if config.GUI.opengl_charts:
                series_spectrum.setUseOpenGL(True)

            getattr(self.ui,
                    f'{series.name}_spectrum_checkbox').stateChanged.connect(
                        self.spectrums_checkboxes_stateChanged)

        ##### Telemetry

        for chart in self.charts:
            # Create Chart and set General Chart setting
            chart.chart = getattr(self.ui, f'{chart.name}_plot').chart()
            chart.chart.legend().hide()
            chart.chart.hovered.connect(self.hover_xy_to_str_charts)

            # X Axis Settings
            axis_x = self.slopes_axis_x = QDateTimeAxis()
            axis_x.setTickCount(5)
            axis_x.setFormat('H:mm:ss')
            # axis_x.setTitleText('Time')
            chart.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)

            # Y Axis Settings
            axis_y = self.slopes_axis_y = QValueAxis()
            axis_y.setTickCount(7)
            axis_y.setRange(0, 1.05)
            axis_y.setTitleText('Amplitude')  # TODO: units
            chart.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

        for series in self.series:
            getattr(self.ui, f'{series.name}_label').setStyleSheet(
                f'color: {series.color.name()}')

            chart = getattr(self.ui, f'{series.chart_name}_plot').chart()
            axis_x = chart.axisX()
            axis_y = chart.axisY()

            pen = QPen(series.color.lighter(125), 1.25, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)

            series_mean = QLineSeries()
            series_mean.setPen(pen)
            series_mean.setName(f'{series.name} mean')
            chart.addSeries(series_mean)
            series_mean.attachAxis(axis_x)
            series_mean.attachAxis(axis_y)

            pen = QPen(series.color.darker(125), 1.25, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)

            series_std = QLineSeries()
            series_std.setPen(pen)
            series_std.setName(f'{series.name} std')
            chart.addSeries(series_std)
            series_std.attachAxis(axis_x)
            series_std.attachAxis(axis_y)

            series.mean_points = [QPointF(0, 0)]
            series.std_points = [QPointF(0, 0)]

            series.mean_series = series_mean
            series.std_series = series_std

            if config.GUI.opengl_charts:
                series_mean.setUseOpenGL(True)
                series_std.setUseOpenGL(True)

            getattr(self.ui,
                    f'{series.name}_mean_checkbox').stateChanged.connect(
                        self.telemetry_checkboxes_stateChanged)
            getattr(self.ui,
                    f'{series.name}_std_checkbox').stateChanged.connect(
                        self.telemetry_checkboxes_stateChanged)

        backend.all_updated.connect(self.all_updated)

    def all_updated(self, data: dict[str, Any]) -> None:
        img = self.consume_shm(data, config.SHM.TELEMETRY_TTM)
        if img is not None:
            df = pd.DataFrame(img.T, columns=config.Telemetry.data_order)
            df['timestamp'] = df['timestamp_0'].astype(
                float) + df['timestamp_1'].astype(float)
            df.drop(['timestamp_0', 'timestamp_1'], axis=1, inplace=True)
            df.index = pd.to_datetime(df['timestamp'], unit='s')
            df.sort_index(inplace=True)

            if self.df_buffer is not None:
                self.df_buffer = pd.concat([
                    self.df_buffer[
                        self.df_buffer.index > df.index[-1] -
                        timedelta(seconds=config.GUI.telemetry_buffer_length)],
                    df[df.index > self.df_buffer.index[-1]]
                ])
            else:
                self.df_buffer = df

            self.update_spectrums(self.df_buffer)
            self.update_telemetry(self.df_buffer)

    def telemetry_checkboxes_stateChanged(self, state: Qt.CheckState) -> None:
        self.update_telemetry()

    @Slot(float)
    def on_binning_spinbox_valueChanged(self, d: float) -> None:
        self.update_telemetry()

    @Slot(float)
    def on_length_spinbox_valueChanged(self, d: float) -> None:
        self.update_telemetry()

    def update_telemetry(self, df: pd.DataFrame | None = None) -> None:
        if df is not None:
            df = df[df.index >= self.last_timestamp].resample(
                f'{self.ui.binning_spinbox.value()}s', label='right',
                closed='right').agg(['mean', 'std'])

            # Add new points

            index = None
            row = None

            # Note: skip last bin as it will have incomplete data
            for index, row in df[:-2].iterrows():
                timestamp_msec = index.timestamp() * 1000

                if timestamp_msec <= self.series[0].mean_points[-1].x():
                    continue

                for series in self.series:
                    series.mean_points.append(
                        QPointF(timestamp_msec,
                                row[series.name]['mean'] * series.scaling))
                    series.std_points.append(
                        QPointF(timestamp_msec,
                                row[series.name]['std'] * series.scaling))

            # Update values displayed in spinboxes (latest value)

            if index is not None:
                for series in self.series:
                    getattr(self.ui, f'{series.name}_mean_spinbox').setValue(
                        row[series.name]['mean'] * series.scaling)
                    getattr(self.ui, f'{series.name}_std_spinbox').setValue(
                        row[series.name]['std'] * series.scaling)

                self.last_timestamp = index

            # Delete old points

            timestamp_msec = time.time() * 1000
            while self.series[0].mean_points[0].x(
            ) < timestamp_msec - self.ui.length_spinbox.value() * 1000:
                for series in self.series:
                    del series.mean_points[0]
                    del series.std_points[0]

        # Update plots

        mins = {}
        maxs = {}
        for chart in self.charts:
            mins[chart.name] = np.inf
            maxs[chart.name] = -np.inf

        for series in self.series:
            if getattr(self.ui, f'{series.name}_mean_checkbox').isChecked():
                for p in series.mean_points:
                    mins[series.chart_name] = min(mins[series.chart_name],
                                                  p.y())
                    maxs[series.chart_name] = max(maxs[series.chart_name],
                                                  p.y())

                series.mean_series.replace(series.mean_points)
            else:
                series.mean_series.replace([])

            if getattr(self.ui, f'{series.name}_std_checkbox').isChecked():
                for p in series.std_points:
                    mins[series.chart_name] = min(mins[series.chart_name],
                                                  p.y())
                    maxs[series.chart_name] = max(maxs[series.chart_name],
                                                  p.y())

                series.std_series.replace(series.std_points)
            else:
                series.std_series.replace([])

        now = QDateTime.currentDateTime()

        for chart in self.charts:
            y_min = mins[chart.name]
            y_max = maxs[chart.name]

            delta = y_max - y_min
            if abs(delta) < config.epsilon:
                y_min -= 0.01
                y_max += 0.01
            else:
                y_min -= 0.05 * delta
                y_max += 0.05 * delta

            chart.chart.axisX().setRange(
                now.addSecs(int(-self.ui.length_spinbox.value())), now)
            chart.chart.axisY().setRange(y_min, y_max)
            chart.chart.axisY().applyNiceNumbers()

    def hover_xy_to_str_charts(self, series: QLineSeries, x: float,
                               y: float) -> None:
        if not np.isnan(x) and not np.isnan(y):
            x = QDateTime.fromMSecsSinceEpoch(
                int(x)).toString('HH:mm:ss dd-MM-yy')

            # TODO: units and precision
            self.hovered.emit(f'{y:.3f} at {x}')
        else:
            self.hovered.emit('')

    def hover_xy_to_str_spectrum(self, series: QLineSeries, x: float,
                                 y: float) -> None:
        if not np.isnan(x) and not np.isnan(y):
            self.hovered.emit(f'Frequency: {x:.1f} Hz, Amplitude: {y:.2f}')
        else:
            self.hovered.emit('')

    def spectrums_checkboxes_stateChanged(self, state: Qt.CheckState) -> None:
        self.update_spectrums()

    def update_spectrums(self, df: pd.DataFrame | None = None) -> None:
        if df is not None:
            dt = np.diff(df['timestamp'].to_numpy()).mean()

            if dt == 0:
                return  # Don't update the graph

            data = df[self.spectrum_key_list].to_numpy().T

            frequency, power = scipy.signal.periodogram(
                data, 1 / dt, scaling='spectrum')
            amplitude = np.sqrt(power)

            for series in self.series:
                if not series.spectrum:
                    continue

                index = self.spectrum_key_list.index(series.name)

                series.spectrum_points = []

                for f, v in zip(frequency[1:], amplitude[index, 1:]):
                    series.spectrum_points.append(QPointF(f, v))

                series.spectrum_max = amplitude[index, :].max()

            self.spectrums_axis_x.setRange(frequency[1], frequency[-1])

        y_max = 0

        for series in self.series:
            if not series.spectrum:
                continue

            if getattr(self.ui,
                       f'{series.name}_spectrum_checkbox').isChecked():
                series.spectrum_series.replace(series.spectrum_points)
                y_max = max(y_max, series.spectrum_max)
            else:
                series.spectrum_series.replace([])

        if y_max < config.epsilon:
            series_min = -0.01
            series_max = 0.01
        else:
            series_min = -0.05 * y_max
            series_max = y_max * 1.05

        self.spectrums_axis_y.setRange(series_min, series_max)
        self.spectrums_axis_y.applyNiceNumbers()
