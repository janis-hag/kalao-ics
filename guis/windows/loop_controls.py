import numpy as np

from PySide6.QtCharts import QLineSeries, QValueAxis
from PySide6.QtCore import QPointF, QSignalBlocker, Signal, Slot
from PySide6.QtGui import Qt

from guis.kalao.mixins import BackendActionMixin, BackendDataMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

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


class LoopControlsWidget(KalAOWidget, BackendActionMixin, BackendDataMixin):
    hovered = Signal(str)

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('loop_controls.ui', self)
        self.resize(600, 400)

        with QSignalBlocker(self.nuvu_emgain_spinbox):
            self.nuvu_emgain_spinbox.setMaximum(config.WFS.max_emgain)

        with QSignalBlocker(self.nuvu_exposuretime_spinbox):
            self.nuvu_exposuretime_spinbox.setMinimum(
                config.WFS.min_exposuretime)

        with QSignalBlocker(self.nuvu_autogain_setting_spinbox):
            self.nuvu_autogain_setting_spinbox.setMaximum(
                config.WFS.max_autogain_setting)

        with QSignalBlocker(self.bmc_strokemode_combobox):
            for mode in config.AO.bmc_stroke_modes:
                self.bmc_strokemode_combobox.addItem(mode)

            self.bmc_strokemode_combobox.setCurrentIndex(-1)

        with QSignalBlocker(self.shwfs_algorithm_combobox):
            for alogrithm in config.AO.shwfs_algorithms:
                self.shwfs_algorithm_combobox.addItem(alogrithm)

            self.shwfs_algorithm_combobox.setCurrentIndex(-1)

        # Create Chart and set General Chart setting
        chart = self.modalgains_plot.chart

        # X Axis Settings
        axis_x = self.axis_x = QValueAxis()
        axis_x.setLabelFormat("%.0f")
        axis_x.setTickAnchor(0)
        axis_x.setTickInterval(10)
        axis_x.setTickType(QValueAxis.TicksDynamic)
        axis_x.setRange(-1, 1)
        chart.addAxis(axis_x, Qt.AlignBottom)

        # Y Axis Settings
        axis_y = self.axis_y = QValueAxis()
        axis_y.setTickAnchor(0)
        axis_y.setTickInterval(0.25)
        axis_y.setTickType(QValueAxis.TicksDynamic)
        axis_y.setRange(-0.05, 1.05)
        chart.addAxis(axis_y, Qt.AlignLeft)

        # Serie
        series = self.modalgains_series = QLineSeries()
        series.setName("Modal gains")
        series.setPointsVisible(True)
        series.pressed.connect(self.on_modalgains_pressed)
        series.released.connect(self.on_modalgains_released)

        series.hovered.connect(lambda point, state, series=self.
                               modalgains_series: self.modalgains_plot.chart.
                               pointHoveredEvent(point, state, series))

        chart.addSeries(series)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        with QSignalBlocker(self.law_combobox):
            for s in laws.keys():
                self.law_combobox.addItem(s)

        self.modalgains_plot.chart.hovered.connect(self.hover_xy_to_str)
        self.modalgains_plot.dragged.connect(self.hover_xy_to_str)

        backend.data_updated.connect(self.data_updated)

    def data_updated(self, data):
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
            self.nuvu_autogain_setting_spinbox)

        # Deformable Mirror

        self.data_to_widget(
            self.consume_param(data, config.FPS.BMC, 'max_stroke'),
            self.bmc_maxstroke_spinbox)
        self.data_to_widget(
            self.consume_param(data, config.FPS.BMC, 'stroke_mode'),
            self.bmc_strokemode_combobox)

        # Slopes

        self.data_to_widget(
            self.consume_param(data, config.FPS.SHWFS, 'algorithm'),
            self.shwfs_algorithm_combobox)

        # Modal gains

        img = self.consume_stream(data, config.Streams.MODALGAINS)

        if img is not None:
            self.display_modalgains(img)

            with QSignalBlocker(self.cutoff_spinbox):
                self.cutoff_spinbox.setMaximum(img.size - 1)
                self.cutoff_spinbox.setValue(img.size - 1)

            with QSignalBlocker(self.last_spinbox):
                self.last_spinbox.setMaximum(img.size - 1)
                self.last_spinbox.setValue(img.size - 1)

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
    def on_nuvu_autogain_setting_spinbox_valueChanged(self, i):
        self.action_send(self.nuvu_autogain_setting_spinbox,
                         self.backend.set_nuvu_autogain_setting, i)

    # Deformable Mirror

    @Slot(float)
    def on_bmc_maxstroke_spinbox_valueChanged(self, d):
        self.action_send(self.bmc_maxstroke_spinbox,
                         self.backend.set_bmc_maxstroke, d)

    @Slot(int)
    def on_bmc_strokemode_combobox_currentIndexChanged(self, index):
        self.action_send(self.bmc_strokemode_combobox,
                         self.backend.set_bmc_strokemode, index)

    # Modal gains

    def on_modalgains_pressed(self, point):
        points = self.modalgains_series.points()

        p, i = self.modalgains_plot.chart.find_closest_point(point, points)

        self.modalgains_plot.chart.current_dragged_series = self.modalgains_series
        self.modalgains_plot.chart.current_dragged_point = p
        self.modalgains_plot.chart.current_dragged_index = i

        self.hovered.emit(f'X: {p.x():.0f}, Y: {p.y():.2f}')

    def on_modalgains_released(self, point):
        self.modalgains_plot.chart.current_dragged_series = None
        self.modalgains_plot.chart.current_dragged_point = None
        self.modalgains_plot.chart.current_dragged_index = None

        self.hovered.emit('')

        modalgains = []
        for point in self.modalgains_series.points():
            modalgains.append(point.y())

        self.action_send([], self.backend.set_modalgains, np.array(modalgains))

    def hover_xy_to_str(self, x, y):
        if not np.isnan(x) and not np.isnan(y):
            self.hovered.emit(f'X: {x:.0f}, Y: {y:.2f}')
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
        cutoff = self.cutoff_spinbox.value()
        last = self.last_spinbox.value()
        law = laws[self.law_combobox.currentText()]

        modalgains = np.ones(self.modalgains_series.count())
        modalgains[cutoff:last + 1] = law(cutoff, last + 1)
        modalgains[last + 1:] = 0

        self.display_modalgains(modalgains)

        self.action_send([], self.backend.set_modalgains, modalgains)

    def display_modalgains(self, modalgains):
        self.modalgains_series.removePoints(0, self.modalgains_series.count())

        for i in range(modalgains.size):
            self.modalgains_series.append(QPointF(i, modalgains[i]))

        self.axis_x.setRange(-1, modalgains.size)
