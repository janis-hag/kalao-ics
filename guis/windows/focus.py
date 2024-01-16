import numpy as np
from numpy.polynomial import Polynomial

from PySide6.QtCharts import (QScatterSeries, QSplineSeries, QValueAxis,
                              QXYSeries)
from PySide6.QtCore import QPointF, QTimer
from PySide6.QtGui import QBrush, QFont, QPen, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

from guis.kalao.definitions import Color
from guis.kalao.mixins import BackendDataMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KGraphicsView, KLabel, KMainWindow

import config


class FocusWindow(KMainWindow, BackendDataMixin):
    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('focus.ui', self)
        self.resize(800, 400)

        self.widgets = {}
        for i in range(config.Focusing.steps):
            vlayout = QVBoxLayout()

            font = QFont()
            font.setBold(True)

            title_label = QLabel(f'Step {i+1}')
            title_label.setFont(font)
            title_label.setAlignment(Qt.AlignHCenter)
            vlayout.addWidget(title_label)

            view = KGraphicsView()
            vlayout.addWidget(view)

            desc_label = KLabel('FWHM {fwhm:.2f}"')
            desc_label.updateText(fwhm=np.nan)
            desc_label.setAlignment(Qt.AlignHCenter)
            vlayout.addWidget(desc_label)

            self.widgets[i + 1] = (view, desc_label)

            self.sequence_layout.addLayout(vlayout, i // 4, i % 4)

        # Create Chart and set General Chart setting
        chart = self.sequence_plot.chart()

        # Serie
        pen = QPen(Color.RED, 1.25, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)

        series_fit = self.focus_fit_series = QSplineSeries()
        series_fit.setPen(pen)
        series_fit.setMarkerSize(6)
        series_fit.setName("Fit")
        series_fit.setPointsVisible(False)
        chart.addSeries(series_fit)

        brush = QBrush(Color.BLUE, Qt.SolidPattern)

        series = self.focus_series = QScatterSeries()
        series.setBrush(brush)
        series.setMarkerSize(6)
        series.setName("Focus Sequence")
        series.setPointsVisible(True)
        chart.addSeries(series)

        # X Axis Settings
        axis_x = self.axis_x = QValueAxis()
        axis_x.setLabelFormat("%.0f")
        axis_x.setTickCount(5)
        axis_x.setRange(0, 4)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        series_fit.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.axis_y = QValueAxis()
        axis_x.setTickCount(5)
        axis_y.setRange(0, 4)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        series_fit.attachAxis(axis_y)

        chart.legend().hide()

        backend.focus_updated.connect(self.focus_updated, Qt.UniqueConnection)

        self.focus_timer = QTimer(parent=self)
        self.focus_timer.setInterval(int(1000 / config.GUI.refreshrate_focus))
        self.focus_timer.timeout.connect(self.backend.get_focus)
        self.focus_timer.start()

        self.show()
        self.center()
        self.setFixedSize(self.size())

    def focus_updated(self, data):
        hdul = self.consume_fits_full(data, 'focus_sequence')

        if hdul is None:
            return

        self.clear()

        for i in range(1, len(hdul)):
            view, desc_label = self.widgets[i]
            view.setImage(hdul[i].data)

            fwhm = hdul[i].header[
                "HIERARCH FOCUS STAR FWHM"] * config.FLI.plate_scale
            focus = hdul[i].header["HIERARCH FOCUS M2 POSITION"]

            desc_label.updateText(fwhm=fwhm)

            self.focus_series.append(QPointF(focus, fwhm))

            x_min = np.inf
            x_max = -np.inf

            y_min = np.inf
            y_max = -np.inf

            for p in self.focus_series.points():
                x_min = min(x_min, p.x())
                x_max = max(x_max, p.x())

                y_min = min(y_min, p.y())
                y_max = max(y_max, p.y())

            x_min -= config.Focusing.step_size
            x_max += config.Focusing.step_size

            self.axis_x.setRange(x_min, x_max)
            self.axis_y.setRange(y_min * 0.8, y_max * 1.2)

        if 'HIERARCH FOCUS FIT QUAD' in hdul[0].header:
            a = hdul[0].header['HIERARCH FOCUS FIT QUAD']
            b = hdul[0].header['HIERARCH FOCUS FIT LIN']
            c = hdul[0].header['HIERARCH FOCUS FIT CONST']

            fit = Polynomial([c, b, a])

            focus_s = np.linspace(x_min, x_max, 25)
            fwhms = fit(focus_s) * config.FLI.plate_scale

            for x, y in zip(focus_s, fwhms):
                self.focus_fit_series.append(QPointF(x, y))

        if 'HIERARCH FOCUS BEST M2 POSITION' in hdul[0].header:
            best_focus = hdul[0].header['HIERARCH FOCUS BEST M2 POSITION']
            best_fwhm = hdul[0].header[
                'HIERARCH FOCUS BEST STAR FWHM'] * config.FLI.plate_scale

            self.focus_series.append(QPointF(best_focus, best_fwhm))
            self.focus_series.setPointConfiguration(
                self.focus_series.count() - 1,
                {QXYSeries.PointConfiguration.Color: Color.GREEN})

    def clear(self):
        self.focus_series.clear()
        self.focus_fit_series.clear()

        self.axis_x.setRange(0, 4)
        self.axis_y.setRange(0, 4)

        for view, desc_label in self.widgets.values():
            view.setImage(None)
            desc_label.updateText(fwhm=np.nan)

    def closeEvent(self, event):
        self.focus_timer.stop()
        self.backend.focus_updated.disconnect(self.focus_updated)
        event.accept()

    def showEvent(self, event):
        self.focus_timer.start()
        self.backend.focus_updated.connect(self.focus_updated,
                                           Qt.UniqueConnection)
        event.accept()
