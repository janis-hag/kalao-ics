import numpy as np
from numpy.polynomial import Polynomial

from astropy.io import fits

from PySide6.QtCharts import (QScatterSeries, QSplineSeries, QValueAxis,
                              QXYSeries)
from PySide6.QtCore import QPointF, QTimer
from PySide6.QtGui import QBrush, QFont, QPen, Qt
from PySide6.QtWidgets import QLabel, QMessageBox, QVBoxLayout

from guis.utils.definitions import Color
from guis.utils.mixins import BackendDataMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KGraphicsView, KLabel, KMainWindow, KMessageBox

import config


class FocusSequenceWindow(KMainWindow, BackendDataMixin):
    def __init__(self, backend, file=None, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.file = file

        loadUi('focus_sequence.ui', self)
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

            desc_label = KLabel('Score {fwhm:.2f}')
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
        axis_x.setTitleText('M2 Position [µm]')
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        series_fit.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.axis_y = QValueAxis()
        axis_y.setTickCount(5)
        axis_y.setTitleText('Score [a.u.]')
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        series_fit.attachAxis(axis_y)

        chart.legend().hide()

        self.clear()
        self.status_label.updateText(status='--')

        if self.file is None:
            backend.focus_sequence_updated.connect(self.focus_sequence_updated,
                                                   Qt.UniqueConnection)

            self.focus_timer = QTimer(parent=self)
            self.focus_timer.setInterval(
                int(1000 / config.GUI.refreshrate_focus))
            self.focus_timer.timeout.connect(self.backend.focus_sequence)
            self.focus_timer.start()
        else:
            self.setWindowTitle(f'{self.file.name} - {self.windowTitle()}')
            hdul = fits.open(self.file)

            if 'HIERARCH KAO FOC SUCCESS' not in hdul[0].header:
                msgbox = KMessageBox(self)
                msgbox.setIcon(QMessageBox.Critical)
                msgbox.setText('<b>Invalid file!</b>')
                msgbox.setInformativeText(
                    'The selected file doesn\'t seem to contain a focus sequence.'
                )
                msgbox.setModal(True)
                msgbox.show()
                self.close()

            self.show_sequence(hdul)

        self.show()
        self.center()
        self.setFixedSize(self.size())

    def focus_sequence_updated(self, data):
        hdul = self.consume_fits_full(data, config.FITS.last_focus_sequence)

        if hdul is not None:
            self.show_sequence(hdul)

    def show_sequence(self, hdul):
        self.clear()

        for i in range(1, len(hdul)):
            view, desc_label = self.widgets[i]
            view.setImage(hdul[i].data)

            fwhm = hdul[i].header[
                "HIERARCH KAO FOC STAR FWHM"] * config.Camera.plate_scale
            focus = hdul[i].header["HIERARCH KAO FOC M2 POS"]

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
                self.status_label.updateText(status='Success!')
                self.status_label.setStyleSheet('')
            else:
                reason = hdul[0].header['HIERARCH KAO FOC REASON']

                self.status_label.updateText(status=reason)
                self.status_label.setStyleSheet(f'color: {Color.RED.name()};')

                if self.file is None:
                    msgbox = KMessageBox(self)
                    msgbox.setIcon(QMessageBox.Critical)
                    msgbox.setText('<b>Focusing failed!</b>')
                    msgbox.setInformativeText(
                        f'Focusing failed with the following error:\n\n{reason}'
                    )
                    msgbox.setModal(True)
                    msgbox.show()
        else:
            self.status_label.updateText(status=f'Step {len(hdul)-1}')
            self.status_label.setStyleSheet('')

    def clear(self):
        self.focus_series.clear()
        self.focus_fit_series.clear()

        self.axis_x.setRange(0, 4)
        self.axis_y.setRange(0, 4)

        for view, desc_label in self.widgets.values():
            view.setImage(None)
            desc_label.updateText(fwhm=np.nan)

    def closeEvent(self, event):
        if self.file is None:
            self.focus_timer.stop()
            self.backend.focus_sequence_updated.disconnect(
                self.focus_sequence_updated)

        event.accept()

    def showEvent(self, event):
        if self.file is None:
            self.focus_timer.start()
            self.backend.focus_sequence_updated.connect(
                self.focus_sequence_updated, Qt.UniqueConnection)
        event.accept()
