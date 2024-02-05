import numpy as np
import scipy.signal

from PySide6.QtCharts import (QBarSeries, QBarSet, QLineSeries, QLogValueAxis,
                              QValueAxis)
from PySide6.QtCore import QPointF, QSignalBlocker, Signal, Slot
from PySide6.QtGui import QPen, Qt

from guis.utils.definitions import Color
from guis.utils.mixins import BackendActionMixin, BackendDataMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KWidget

import config

laws = {
    'Linear':
        lambda start, end: np.linspace(1, 0, end - start),
    'Quadratic':
        lambda start, end: np.linspace(1, 0, end - start)**2,
    'Square root':
        lambda start, end: np.linspace(1, 0, end - start)**0.5,
    'Exponential1':
        lambda start, end: 10**(np.linspace(0, -10, end - start)),
    'Exponential2':
        lambda start, end: 10**(np.linspace(0, -3, end - start)),
    'Exponential3':
        lambda start, end: 2**(np.linspace(0, -10, end - start)),
    'Exponential4':
        lambda start, end: 2**(np.linspace(0, -3, end - start)),
    'Logarithmic':
        lambda start, end: np.log10(np.linspace(10, 1, end - start)),
}


class LoopControlsWidget(KWidget, BackendActionMixin, BackendDataMixin):
    hovered = Signal(str)

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('loop_controls.ui', self)
        self.resize(600, 400)

        with QSignalBlocker(self.nuvu_emgain_spinbox):
            self.nuvu_emgain_spinbox.setMinimum(config.WFS.min_emgain)
            self.nuvu_emgain_spinbox.setMaximum(config.WFS.max_emgain)

        with QSignalBlocker(self.nuvu_exposuretime_spinbox):
            self.nuvu_exposuretime_spinbox.setMinimum(
                config.WFS.min_exposuretime)
            self.nuvu_exposuretime_spinbox.setMaximum(
                config.WFS.max_exposuretime)

        with QSignalBlocker(self.nuvu_autogain_setting_combobox):
            for emgain, exptime in config.WFS.autogain_params:
                self.nuvu_autogain_setting_combobox.addItem(
                    f'EM Gain: {emgain:d}, Exp. time: {exptime:.1f} ms')

            self.nuvu_autogain_setting_combobox.setCurrentIndex(-1)

        with QSignalBlocker(self.bmc_strokemode_combobox):
            for mode in config.AO.bmc_stroke_modes:
                self.bmc_strokemode_combobox.addItem(mode)

            self.bmc_strokemode_combobox.setCurrentIndex(-1)

        with QSignalBlocker(self.shwfs_algorithm_combobox):
            for alogrithm in config.AO.shwfs_algorithms:
                self.shwfs_algorithm_combobox.addItem(alogrithm)

            self.shwfs_algorithm_combobox.setCurrentIndex(-1)

        # Create Chart and set General Chart setting
        chart = self.modalgains_plot.chart()

        # Serie
        pen = QPen(Color.BLUE, 1.25, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)

        series = self.modalgains_series = QLineSeries()
        series.setPen(pen)
        series.setMarkerSize(chart.point_size)
        series.setName("Modal gains")
        series.setPointsVisible(True)
        series.pressed.connect(self.on_modalgains_pressed)
        series.released.connect(self.on_modalgains_released)
        chart.addSeries(series)

        # X Axis Settings
        axis_x = self.modalgains_axis_x = QValueAxis()
        axis_x.setLabelFormat("%.0f")
        axis_x.setTickAnchor(0)
        axis_x.setTickInterval(10)
        axis_x.setTickType(QValueAxis.TicksDynamic)
        axis_x.setRange(0, 1)
        axis_x.setTitleText('Mode [-]')
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.modalgains_axis_y = QValueAxis()
        axis_y.setTickAnchor(0)
        axis_y.setTickInterval(0.25)
        axis_y.setTickType(QValueAxis.TicksDynamic)
        axis_y.setRange(-0.05, 1.05)
        axis_y.setTitleText('Gain [-]')
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().hide()

        series.hovered.connect(lambda point, state, series=self
                               .modalgains_series: self.modalgains_plot.chart(
                               ).pointHoveredEvent(point, state, series))

        with QSignalBlocker(self.law_combobox):
            for s in laws.keys():
                self.law_combobox.addItem(s)

        chart.hovered.connect(self.hover_xy_to_str)
        self.modalgains_plot.dragged.connect(self.hover_xy_to_str)

        # Create Chart and set General Chart setting
        chart = self.modes_plot.chart()

        # Serie
        series = self.modes_series = QBarSeries()
        series.setName("Mode Coefficients")
        chart.addSeries(series)

        series_line = self.modes_series_line = QLineSeries()
        chart.addSeries(series_line)

        # X Axis Settings
        axis_x = self.modes_axis_x = QValueAxis()
        axis_x.setLabelFormat("%.0f")
        axis_x.setTickAnchor(0)
        axis_x.setTickInterval(10)
        axis_x.setTickType(QValueAxis.TicksDynamic)
        axis_x.setRange(0, 1)
        axis_x.setTitleText('Mode [-]')
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        series_line.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.modes_axis_y = QValueAxis()
        axis_y.setTickCount(7)
        axis_y.setRange(-1.05, 1.05)
        axis_y.setTitleText('Coefficient [µm RMS]')
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        series_line.attachAxis(axis_y)

        chart.legend().hide()

        # Create Chart and set General Chart setting
        chart = self.tiptilt_spectrum_plot.chart()

        # Serie
        pen = QPen(Color.BLUE, 1.25, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)

        series_tip = self.tip_spectrum_series = QLineSeries()
        series_tip.setPen(pen)
        series_tip.setMarkerSize(chart.point_size)
        series_tip.setName("Tilt Spectrum")
        series_tip.setPointsVisible(True)
        chart.addSeries(series_tip)

        # Serie
        pen = QPen(Color.RED, 1.25, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)

        series_tilt = self.tilt_spectrum_series = QLineSeries()
        series_tilt.setPen(pen)
        series_tilt.setMarkerSize(chart.point_size)
        series_tilt.setName("Tilt Spectrum")
        series_tilt.setPointsVisible(True)
        chart.addSeries(series_tilt)

        # X Axis Settings
        axis_x = self.tiptilt_spectrum_axis_x = QLogValueAxis()
        axis_x.setBase(10)
        axis_x.setRange(self.tiptilt_min_freq, self.tiptilt_max_freq)
        axis_x.setTitleText('Frequency [Hz]')
        chart.addAxis(axis_x, Qt.AlignBottom)
        series_tip.attachAxis(axis_x)
        series_tilt.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.tiptilt_spectrum_axis_y = QValueAxis()
        axis_y.setTickCount(7)
        axis_y.setRange(0, 1.05)
        axis_y.setTitleText('Amplitude [a.u.]')
        chart.addAxis(axis_y, Qt.AlignLeft)
        series_tip.attachAxis(axis_y)
        series_tilt.attachAxis(axis_y)

        chart.legend().hide()

        backend.all_updated.connect(self.all_updated)
        backend.streams_all_updated.connect(self.streams_all_updated)

    def all_updated(self, data):
        # DM Loop

        self.data_to_widget(
            self.consume_dict(data, config.FPS.DMLOOP, 'loopON'),
            self.dmloop_on_checkbox, true_value=True)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.DMLOOP, 'loopgain'),
            self.dmloop_gain_spinbox)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.DMLOOP, 'loopmult'),
            self.dmloop_mult_spinbox)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.DMLOOP, 'looplimit'),
            self.dmloop_limit_spinbox)

        # TTM Loop

        self.data_to_widget(
            self.consume_dict(data, config.FPS.TTMLOOP, 'loopON'),
            self.ttmloop_on_checkbox, true_value=True)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.TTMLOOP, 'loopgain'),
            self.ttmloop_gain_spinbox)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.TTMLOOP, 'loopmult'),
            self.ttmloop_mult_spinbox)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.TTMLOOP, 'looplimit'),
            self.ttmloop_limit_spinbox)

        # Wavefront Sensor

        self.data_to_widget(
            self.consume_stream_keyword(data, config.Streams.NUVU_RAW,
                                        'EMGAIN'), self.nuvu_emgain_spinbox)
        self.data_to_widget(
            self.consume_stream_keyword(data, config.Streams.NUVU_RAW,
                                        'EXPTIME'),
            self.nuvu_exposuretime_spinbox)
        self.data_to_widget(
            self.consume_param(data, config.FPS.NUVU, 'autogain_on'),
            self.nuvu_autogain_checkbox, true_value=True)
        self.data_to_widget(
            self.consume_param(data, config.FPS.NUVU, 'autogain_setting'),
            self.nuvu_autogain_setting_combobox)

        # Deformable Mirror

        max_stroke = self.consume_param(data, config.FPS.BMC, 'max_stroke')
        if max_stroke is not None:
            with QSignalBlocker(self.bmc_maxstroke_spinbox):
                self.bmc_maxstroke_spinbox.setValue(max_stroke * 100)

        self.data_to_widget(
            self.consume_param(data, config.FPS.BMC, 'stroke_mode'),
            self.bmc_strokemode_combobox)

        target_stroke = self.consume_param(data, config.FPS.BMC,
                                           'target_stroke')
        if target_stroke is not None:
            with QSignalBlocker(self.bmc_targetstroke_spinbox):
                self.bmc_targetstroke_spinbox.setValue(target_stroke * 100)

        # Slopes

        self.data_to_widget(
            self.consume_param(data, config.FPS.SHWFS, 'algorithm'),
            self.shwfs_algorithm_combobox)

        # Modal gains

        img = self.consume_stream(data, config.Streams.MODALGAINS)
        if img is not None:
            if img.size != self.modalgains_series.count():
                with QSignalBlocker(self.cutoff_spinbox):
                    self.cutoff_spinbox.setMaximum(img.size)
                    self.cutoff_spinbox.setValue(img.size)

                with QSignalBlocker(self.last_spinbox):
                    self.last_spinbox.setMinimum(img.size)
                    self.last_spinbox.setMaximum(img.size)
                    self.last_spinbox.setValue(img.size)

            self.display_modalgains(img)

    def streams_all_updated(self, data):
        img = self.consume_stream(data, config.Streams.MODE_COEFFS)
        if img is not None:
            self.display_modes_coeff(img)

        img = self.consume_stream(data, config.Streams.TELEMETRY_TTM)
        if img is not None:
            self.display_tiptilt_spectrum(img)

    # DM Loop

    @Slot(int)
    def on_dmloop_on_checkbox_stateChanged(self, state):
        self.action_send(self.dmloop_on_checkbox, self.backend.set_dmloop_on,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(float)
    def on_dmloop_gain_spinbox_valueChanged(self, d):
        self.action_send(self.dmloop_gain_spinbox,
                         self.backend.set_dmloop_gain, d)

    @Slot(float)
    def on_dmloop_mult_spinbox_valueChanged(self, d):
        self.action_send(self.dmloop_mult_spinbox,
                         self.backend.set_dmloop_mult, d)

    @Slot(float)
    def on_dmloop_limit_spinbox_valueChanged(self, d):
        self.action_send(self.dmloop_limit_spinbox,
                         self.backend.set_dmloop_limit, d)

    @Slot(bool)
    def on_dmloop_zero_button_clicked(self, checked):
        self.action_send(self.dmloop_zero_button, self.backend.get_dmloop_zero)

    # TTM Loop

    @Slot(int)
    def on_ttmloop_on_checkbox_stateChanged(self, state):
        self.action_send(self.ttmloop_on_checkbox, self.backend.set_ttmloop_on,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(float)
    def on_ttmloop_gain_spinbox_valueChanged(self, d):
        self.action_send(self.ttmloop_gain_spinbox,
                         self.backend.set_ttmloop_gain, d)

    @Slot(float)
    def on_ttmloop_mult_spinbox_valueChanged(self, d):
        self.action_send(self.ttmloop_mult_spinbox,
                         self.backend.set_ttmloop_mult, d)

    @Slot(float)
    def on_ttmloop_limit_spinbox_valueChanged(self, d):
        self.action_send(self.ttmloop_limit_spinbox,
                         self.backend.set_ttmloop_limit, d)

    @Slot(bool)
    def on_ttmloop_zero_button_clicked(self, checked):
        self.action_send(self.ttmloop_zero_button,
                         self.backend.get_ttmloop_zero)

    # Wavefront Sensor

    @Slot(int)
    def on_nuvu_emgain_spinbox_valueChanged(self, i):
        self.action_send(self.nuvu_emgain_spinbox,
                         self.backend.set_nuvu_emgain, i)

    @Slot(float)
    def on_nuvu_exposuretime_spinbox_valueChanged(self, d):
        self.action_send(self.nuvu_exposuretime_spinbox,
                         self.backend.set_nuvu_exposuretime, d)

    @Slot(int)
    def on_nuvu_autogain_checkbox_stateChanged(self, state):
        self.action_send(self.nuvu_autogain_checkbox,
                         self.backend.set_nuvu_autogain_on,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(int)
    def on_nuvu_autogain_setting_combobox_currentIndexChanged(self, index):
        self.action_send(self.nuvu_autogain_setting_combobox,
                         self.backend.set_nuvu_autogain_setting, index)

    # Deformable Mirror

    @Slot(float)
    def on_bmc_maxstroke_spinbox_valueChanged(self, d):
        self.action_send(self.bmc_maxstroke_spinbox,
                         self.backend.set_bmc_maxstroke, d / 100)

    @Slot(int)
    def on_bmc_strokemode_combobox_currentIndexChanged(self, index):
        self.action_send(self.bmc_strokemode_combobox,
                         self.backend.set_bmc_strokemode, index)

    @Slot(float)
    def on_bmc_targetstroke_spinbox_valueChanged(self, d):
        self.action_send(self.bmc_targetstroke_spinbox,
                         self.backend.set_bmc_targetstroke, d / 100)

    # Modal gains

    def on_modalgains_pressed(self, point):
        points = self.modalgains_series.points()
        chart = self.modalgains_plot.chart()

        p, i = chart.find_closest_point(point, points)

        chart.current_dragged_series = self.modalgains_series
        chart.current_dragged_point = p
        chart.current_dragged_index = i

        self.hovered.emit(f'Mode: {p.x():.0f}, Gain: {p.y():.2f}')

    def on_modalgains_released(self, point):
        chart = self.modalgains_plot.chart()

        chart.current_dragged_series = None
        chart.current_dragged_point = None
        chart.current_dragged_index = None

        self.hovered.emit('')

        modalgains = []
        for point in self.modalgains_series.points():
            modalgains.append(point.y())

        self.action_send([], self.backend.set_modalgains, np.array(modalgains))

    def hover_xy_to_str(self, x, y):
        if not np.isnan(x) and not np.isnan(y):
            self.hovered.emit(f'Mode: {x:.0f}, Gain: {y:.2f}')
        else:
            self.hovered.emit(f'')

    @Slot(int)
    def on_cutoff_spinbox_valueChanged(self, i):
        self.last_spinbox.setMinimum(i)
        self.compute_modalgains()

    @Slot(int)
    def on_last_spinbox_valueChanged(self, i):
        self.cutoff_spinbox.setMaximum(i)
        self.compute_modalgains()

    @Slot(int)
    def on_law_combobox_currentIndexChanged(self, index):
        self.compute_modalgains()

    def compute_modalgains(self):
        cutoff = self.cutoff_spinbox.value() - 1
        last = self.last_spinbox.value() - 1
        law = laws[self.law_combobox.currentText()]

        modalgains = np.ones(self.modalgains_series.count())
        modalgains[cutoff:last + 1] = law(cutoff, last + 1)
        modalgains[last + 1:] = 0

        self.display_modalgains(modalgains)

        self.action_send([], self.backend.set_modalgains, modalgains)

    def display_modalgains(self, modalgains):
        points = []
        for i in range(modalgains.size):
            points.append(QPointF(i + 1, modalgains[i]))

        self.modalgains_series.replace(points)
        self.modalgains_axis_x.setRange(0, modalgains.size + 1)

    def display_modes_coeff(self, modes_coeff):
        set = QBarSet(f'Mode Coefficients')

        # Add zero coeff. to shift the graph
        set.append(0)

        for i in range(modes_coeff.size):
            set.append(modes_coeff[i])

        self.modes_series.clear()
        self.modes_series.append(set)

        series_min = modes_coeff.min()
        series_max = modes_coeff.max()

        abs_max = max(abs(series_min), abs(series_max))
        series_min = -abs_max * 1.05
        series_max = abs_max * 1.05

        self.modes_axis_x.setRange(0, modes_coeff.size + 1)
        self.modes_axis_y.setRange(series_min, series_max)

    def display_tiptilt_spectrum(self, tiptilt_data):
        jumps = np.argwhere(np.diff(tiptilt_data[0, :]) < 0)
        if len(jumps) > 0:
            shift = jumps[0][0]
            tiptilt_data = np.roll(tiptilt_data, -(shift + 1), axis=1)

        dt = np.diff(tiptilt_data[0, :]).mean()
        frequency, power = scipy.signal.periodogram(tiptilt_data[1:, :],
                                                    1 / dt, scaling='spectrum')
        amplitude = np.sqrt(power)

        points_tip = []
        points_tilt = []
        for f, a_tip, a_tilt in zip(frequency[1:], amplitude[0, 1:],
                                    amplitude[1, 1:]):
            points_tip.append(QPointF(f, a_tip))
            points_tilt.append(QPointF(f, a_tilt))

        self.tip_spectrum_series.replace(points_tip)
        self.tilt_spectrum_series.replace(points_tilt)

        max = amplitude.max()

        self.tiptilt_spectrum_axis_x.setRange(frequency[1], frequency[-1])
        self.tiptilt_spectrum_axis_y.setRange(-0.05 * max, max * 1.05)
