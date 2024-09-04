from pathlib import Path
from typing import Any

import numpy as np
from numpy.polynomial import Polynomial

from astropy.io import fits

from PySide6.QtCharts import (QScatterSeries, QSplineSeries, QValueAxis,
                              QXYSeries)
from PySide6.QtCore import QPointF, QTimer
from PySide6.QtGui import QBrush, QCloseEvent, QFont, QPen, QShowEvent, Qt
from PySide6.QtWidgets import QLabel, QMessageBox, QVBoxLayout, QWidget

from compiled.ui_focus_sequence import Ui_FocusSequenceWindow

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.widgets import (KImageViewer, KLabel, KMainWindow,
                                      KMessageBox)

import config


class FocusSequenceWindow(KMainWindow, BackendDataMixin):
    def __init__(self, backend: AbstractBackend, mainwindow=None,
                 file: Path = None, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend
        self.file = file

        self.ui = Ui_FocusSequenceWindow()
        self.ui.setupUi(self)

        self.resize(800, 400)

        self.sequence_widgets = []

        # Create Chart and set General Chart setting
        chart = self.ui.sequence_plot.chart()
        chart.legend().hide()

        # Serie
        pen = QPen(Color.RED, 1.25, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)

        series_fit = self.focus_fit_series = QSplineSeries()
        series_fit.setPen(pen)
        series_fit.setMarkerSize(6)
        series_fit.setName('Fit')
        series_fit.setPointsVisible(False)
        chart.addSeries(series_fit)

        brush = QBrush(Color.BLUE, Qt.BrushStyle.SolidPattern)

        series = self.focus_series = QScatterSeries()
        series.setBrush(brush)
        series.setMarkerSize(6)
        series.setName('Focus Sequence')
        series.setPointsVisible(True)
        chart.addSeries(series)

        # X Axis Settings
        axis_x = self.axis_x = QValueAxis()
        axis_x.setLabelFormat('%.0f')
        axis_x.setTickCount(5)
        axis_x.setTitleText('M2 Position [µm]')
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        series_fit.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.axis_y = QValueAxis()
        axis_y.setTickCount(5)
        axis_y.setTitleText('Score [a.u.]')
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        series_fit.attachAxis(axis_y)

        self.clear()
        self.ui.status_label.updateText(status='--')

        if self.file is None:
            backend.focusing_sequence_fits_updated.connect(
                self.focusing_sequence_fits_updated)

            self.create_widgets(config.Focusing.nexp)

            self.focus_timer = QTimer(parent=self)
            self.focus_timer.setInterval(
                int(1000 / config.GUI.refreshrate_auxillary))
            self.focus_timer.timeout.connect(backend.focusing_sequence_fits)
            self.focus_timer.start()
        else:
            self.setWindowTitle(f'{self.file.name} - {self.windowTitle()}')

            hdul = fits.open(self.file)
            self.create_widgets(len(hdul) - 1)
            self.show_sequence(hdul)

        self.show()
        self.center()
        self.setFixedSize(self.size())

    def create_widgets(self, length: int) -> None:
        for i in range(length):
            vlayout = QVBoxLayout()

            font = QFont()
            font.setBold(True)

            title_label = QLabel(f'Step {i+1}')
            title_label.setFont(font)
            title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vlayout.addWidget(title_label)

            view = KImageViewer()
            vlayout.addWidget(view)

            label = KLabel('Score {fwhm:.2f}')
            label.updateText(fwhm=np.nan)
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vlayout.addWidget(label)

            self.ui.sequence_layout.addLayout(vlayout, i // 4, i % 4)

            self.sequence_widgets.append({'view': view, 'label': label})

    def focusing_sequence_fits_updated(self, data: dict[str, Any]) -> None:
        hdul = self.consume_fits_full(data, config.FITS.last_focus_sequence)

        if hdul is not None:
            self.show_sequence(hdul)

    def show_sequence(self, hdul: fits.HDUList) -> None:
        self.clear()

        for i in range(1, len(hdul)):
            self.sequence_widgets[i - 1]['view'].setImage(hdul[i].data)

            fwhm = hdul[i].header[
                'HIERARCH KAO FOC STAR FWHM'] * config.Camera.plate_scale
            focus = hdul[i].header['HIERARCH KAO FOC M2 POS']

            self.sequence_widgets[i - 1]['label'].updateText(fwhm=fwhm)

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

        if 'HIERARCH KAO FOC FIT QUAD' in hdul[0].header:
            a = hdul[0].header['HIERARCH KAO FOC FIT QUAD']
            b = hdul[0].header['HIERARCH KAO FOC FIT LIN']
            c = hdul[0].header['HIERARCH KAO FOC FIT CONST']

            fit = Polynomial([c, b, a])

            focus_s = np.linspace(x_min, x_max, 25)
            fwhms = fit(focus_s) * config.Camera.plate_scale

            for x, y in zip(focus_s, fwhms):
                self.focus_fit_series.append(QPointF(x, y))

        if 'HIERARCH KAO FOC BEST M2 POS' in hdul[0].header:
            best_focus = hdul[0].header['HIERARCH KAO FOC BEST M2 POS']
            best_fwhm = hdul[0].header[
                'HIERARCH KAO FOC BEST STAR FWHM'] * config.Camera.plate_scale

            self.focus_series.append(QPointF(best_focus, best_fwhm))
            self.focus_series.setPointConfiguration(
                self.focus_series.count() - 1,
                {QXYSeries.PointConfiguration.Color: Color.GREEN})

        if 'HIERARCH KAO FOC SUCCESS' in hdul[0].header:
            sucess = hdul[0].header['HIERARCH KAO FOC SUCCESS']

            if self.file is None:
                # Stop timer to spare resources
                self.focus_timer.stop()

            if sucess:
                self.ui.status_label.updateText(status='Success!')
                self.ui.status_label.setStyleSheet('')
            else:
                reason = hdul[0].header['HIERARCH KAO FOC REASON']

                self.ui.status_label.updateText(status=reason)
                self.ui.status_label.setStyleSheet(
                    f'color: {Color.RED.name()};')

                if self.file is None:
                    msgbox = KMessageBox(self)
                    msgbox.setIcon(QMessageBox.Icon.Critical)
                    msgbox.setText('<b>Focusing failed!</b>')
                    msgbox.setInformativeText(
                        f'Focusing failed with the following error:\n\n{reason}'
                    )
                    msgbox.setModal(True)
                    msgbox.show()
        else:
            self.ui.status_label.updateText(status=f'Step {len(hdul)-1}')
            self.ui.status_label.setStyleSheet('')

    def clear(self) -> None:
        self.focus_series.clear()
        self.focus_fit_series.clear()

        self.axis_x.setRange(0, 4)
        self.axis_y.setRange(0, 4)

        for widget in self.sequence_widgets:
            widget['view'].setImage(None)
            widget['label'].updateText(fwhm=np.nan)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.file is None:
            self.focus_timer.stop()

        return super().closeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        if self.file is None:
            self.focus_timer.start()

        return super().showEvent(event)
