from typing import Any

import numpy as np

from PySide6.QtCharts import QBarSeries, QBarSet, QLineSeries, QValueAxis
from PySide6.QtCore import QPointF, QSignalBlocker, Signal, Slot
from PySide6.QtGui import QBrush, QPen, Qt
from PySide6.QtWidgets import QWidget

from compiled.ui_loop_controls import Ui_LoopControlsWidget

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendActionMixin, BackendDataMixin
from kalao.guis.utils.widgets import KWidget

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

    plot_length = config.GUI.ttm_plot_length * 1000

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend

        self.ui = Ui_LoopControlsWidget()
        self.ui.setupUi(self)

        self.resize(600, 400)

        with QSignalBlocker(self.ui.wfs_emgain_spinbox):
            self.ui.wfs_emgain_spinbox.setMinimum(config.WFS.min_emgain)
            self.ui.wfs_emgain_spinbox.setMaximum(config.WFS.max_emgain)

        with QSignalBlocker(self.ui.wfs_exposuretime_spinbox):
            self.ui.wfs_exposuretime_spinbox.setMinimum(
                config.WFS.min_exposuretime)
            self.ui.wfs_exposuretime_spinbox.setMaximum(
                config.WFS.max_exposuretime)

        with QSignalBlocker(self.ui.wfs_autogain_setting_combobox):
            for emgain, exptime in config.WFS.autogain_params:
                self.ui.wfs_autogain_setting_combobox.addItem(
                    f'EM Gain: {emgain:d}, Exp. time: {exptime:.3g} ms')

            self.ui.wfs_autogain_setting_combobox.setCurrentIndex(-1)

        with QSignalBlocker(self.ui.dm_strokemode_combobox):
            for mode in config.AO.dm_stroke_modes:
                self.ui.dm_strokemode_combobox.addItem(mode)

            self.ui.dm_strokemode_combobox.setCurrentIndex(-1)

        with QSignalBlocker(self.ui.wfs_algorithm_combobox):
            for alogrithm in config.AO.wfs_algorithms:
                self.ui.wfs_algorithm_combobox.addItem(alogrithm)

            self.ui.wfs_algorithm_combobox.setCurrentIndex(-1)

        # Create Chart and set General Chart setting
        chart = self.ui.modalgains_plot.chart()
        chart.legend().hide()

        # Serie
        pen = QPen(Color.BLUE, 1.25, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)

        series = self.modalgains_series = QLineSeries()
        series.setPen(pen)
        series.setMarkerSize(chart.point_size)
        series.setName('Modal gains')
        series.setPointsVisible(True)
        series.pressed.connect(self.on_modalgains_pressed)
        series.released.connect(self.on_modalgains_released)
        chart.addSeries(series)

        # if config.GUI.opengl_charts:
        #     series.setUseOpenGL(True)

        # X Axis Settings
        axis_x = self.modalgains_axis_x = QValueAxis()
        axis_x.setLabelFormat('%.0f')
        axis_x.setTickAnchor(0)
        axis_x.setTickInterval(10)
        axis_x.setTickType(QValueAxis.TickType.TicksDynamic)
        axis_x.setRange(0, 1)
        axis_x.setTitleText('Mode [-]')
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.modalgains_axis_y = QValueAxis()
        axis_y.setTickAnchor(0)
        axis_y.setTickInterval(0.25)
        axis_y.setTickType(QValueAxis.TickType.TicksDynamic)
        axis_y.setRange(-0.05, 1.05)
        axis_y.setTitleText('Gain [-]')
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        series.hovered.connect(lambda point, state, series=self.
                               modalgains_series: self.ui.modalgains_plot.
                               chart().pointHoveredEvent(point, state, series))

        with QSignalBlocker(self.ui.law_combobox):
            for s in laws.keys():
                self.ui.law_combobox.addItem(s)

        chart.hovered.connect(self.hover_xy_to_str_modalgains)
        self.ui.modalgains_plot.dragged.connect(
            self.hover_xy_to_str_modalgains)

        # Create Chart and set General Chart setting
        chart = self.ui.modes_plot.chart()
        chart.legend().hide()

        # Serie
        series = self.modes_series = QBarSeries()
        series.setName('Mode Coefficients')
        chart.addSeries(series)

        series_line = self.modes_series_line = QLineSeries()
        chart.addSeries(series_line)

        # if config.GUI.opengl_charts:
        #     series.setUseOpenGL(True)
        #     series_line.setUseOpenGL(True)

        # X Axis Settings
        axis_x = self.modes_axis_x = QValueAxis()
        axis_x.setLabelFormat('%.0f')
        axis_x.setTickAnchor(0)
        axis_x.setTickInterval(10)
        axis_x.setTickType(QValueAxis.TickType.TicksDynamic)
        axis_x.setRange(0, 1)
        axis_x.setTitleText('Mode [-]')
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        series_line.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.modes_axis_y = QValueAxis()
        axis_y.setTickCount(7)
        axis_y.setRange(-1.05, 1.05)
        axis_y.setTitleText('Coefficient [µm RMS]')
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        series_line.attachAxis(axis_y)

        chart.hovered.connect(self.hover_xy_to_str_modes_coeffs)

        backend.all_updated.connect(self.all_updated)
        backend.streams_all_updated.connect(self.streams_all_updated)

    def all_updated(self, data: dict[str, Any]) -> None:
        # DM Loop

        md = self.consume_fps_md(data, config.FPS.DMLOOP)
        if md is not None:
            self.ui.dmloop_groupbox.setEnabled('C' in md['status'])

        self.data_to_widget(
            self.consume_dict(data, config.FPS.DMLOOP, 'loopON'),
            self.ui.dmloop_on_checkbox)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.DMLOOP, 'loopgain'),
            self.ui.dmloop_gain_spinbox)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.DMLOOP, 'loopmult'),
            self.ui.dmloop_mult_spinbox)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.DMLOOP, 'looplimit'),
            self.ui.dmloop_limit_spinbox)

        # TTM Loop

        md = self.consume_fps_md(data, config.FPS.TTMLOOP)
        if md is not None:
            self.ui.ttmloop_groupbox.setEnabled('C' in md['status'])

        self.data_to_widget(
            self.consume_dict(data, config.FPS.TTMLOOP, 'loopON'),
            self.ui.ttmloop_on_checkbox)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.TTMLOOP, 'loopgain'),
            self.ui.ttmloop_gain_spinbox)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.TTMLOOP, 'loopmult'),
            self.ui.ttmloop_mult_spinbox)
        self.data_to_widget(
            self.consume_dict(data, config.FPS.TTMLOOP, 'looplimit'),
            self.ui.ttmloop_limit_spinbox)

        # Wavefront Sensor

        md = self.consume_fps_md(data, config.FPS.NUVU)
        if md is not None:
            self.ui.wfs_groupbox.setEnabled('C' in md['status'])

        self.data_to_widget(
            self.consume_shm_keyword(data, config.SHM.NUVU_RAW, 'EMGAIN'),
            self.ui.wfs_emgain_spinbox)
        self.data_to_widget(
            self.consume_shm_keyword(data, config.SHM.NUVU_RAW, 'EXPTIME'),
            self.ui.wfs_exposuretime_spinbox)
        self.data_to_widget(
            self.consume_fps_param(data, config.FPS.NUVU, 'autogain_on'),
            self.ui.wfs_autogain_checkbox)
        self.data_to_widget(
            self.consume_fps_param(data, config.FPS.NUVU, 'autogain_setting'),
            self.ui.wfs_autogain_setting_combobox)

        # Deformable Mirror

        md = self.consume_fps_md(data, config.FPS.BMC)
        if md is not None:
            self.ui.dm_groupbox.setEnabled('C' in md['status'])

        max_stroke = self.consume_fps_param(data, config.FPS.BMC, 'max_stroke')
        if max_stroke is not None:
            with QSignalBlocker(self.ui.dm_maxstroke_spinbox):
                self.ui.dm_maxstroke_spinbox.setValue(max_stroke * 100)

        self.data_to_widget(
            self.consume_fps_param(data, config.FPS.BMC, 'stroke_mode'),
            self.ui.dm_strokemode_combobox)

        target_stroke = self.consume_fps_param(data, config.FPS.BMC,
                                               'target_stroke')
        if target_stroke is not None:
            with QSignalBlocker(self.ui.dm_targetstroke_spinbox):
                self.ui.dm_targetstroke_spinbox.setValue(target_stroke * 100)

        # Observation

        self.data_to_widget(
            self.consume_dict(data, 'memory', 'adc_synchronisation'),
            self.ui.adc_synchronisation_checkbox)
        self.data_to_widget(
            self.consume_dict(data, 'memory', 'ttm_offloading'),
            self.ui.ttm_offloading_checkbox)

        # Slopes

        self.data_to_widget(
            self.consume_fps_param(data, config.FPS.SHWFS, 'algorithm'),
            self.ui.wfs_algorithm_combobox)

        # Modal gains

        img = self.consume_shm(data, config.SHM.MODALGAINS)
        if img is not None:
            if img.size != self.modalgains_series.count():
                with QSignalBlocker(self.ui.cutoff_spinbox):
                    self.ui.cutoff_spinbox.setMaximum(img.size)
                    self.ui.cutoff_spinbox.setValue(img.size)

                with QSignalBlocker(self.ui.last_spinbox):
                    self.ui.last_spinbox.setMinimum(img.size)
                    self.ui.last_spinbox.setMaximum(img.size)
                    self.ui.last_spinbox.setValue(img.size)

            self.display_modalgains(img)

    def streams_all_updated(self, data: dict[str, Any]) -> None:
        img = self.consume_shm(data, config.SHM.MODE_COEFFS)
        if img is not None:
            self.display_modes_coeff(img)

    # DM Loop

    @Slot(int)
    def on_dmloop_on_checkbox_stateChanged(self, state: Qt.CheckState) -> None:
        self.action_send(self.ui.dmloop_on_checkbox, self.backend.ao_dmloop_on,
                         state=Qt.CheckState(state) == Qt.CheckState.Checked)

    @Slot(float)
    def on_dmloop_gain_spinbox_valueChanged(self, d: float) -> None:
        self.action_send(self.ui.dmloop_gain_spinbox,
                         self.backend.ao_dmloop_gain, gain=d)

    @Slot(float)
    def on_dmloop_mult_spinbox_valueChanged(self, d: float) -> None:
        self.action_send(self.ui.dmloop_mult_spinbox,
                         self.backend.ao_dmloop_mult, mult=d)

    @Slot(float)
    def on_dmloop_limit_spinbox_valueChanged(self, d: float) -> None:
        self.action_send(self.ui.dmloop_limit_spinbox,
                         self.backend.ao_dmloop_limit, limit=d)

    @Slot(bool)
    def on_dmloop_zero_button_clicked(self, checked: bool) -> None:
        self.action_send(self.ui.dmloop_zero_button,
                         self.backend.ao_dmloop_zero)

    # TTM Loop

    @Slot(int)
    def on_ttmloop_on_checkbox_stateChanged(self,
                                            state: Qt.CheckState) -> None:
        self.action_send(self.ui.ttmloop_on_checkbox,
                         self.backend.ao_ttmloop_on,
                         state=Qt.CheckState(state) == Qt.CheckState.Checked)

    @Slot(float)
    def on_ttmloop_gain_spinbox_valueChanged(self, d: float) -> None:
        self.action_send(self.ui.ttmloop_gain_spinbox,
                         self.backend.ao_ttmloop_gain, gain=d)

    @Slot(float)
    def on_ttmloop_mult_spinbox_valueChanged(self, d: float) -> None:
        self.action_send(self.ui.ttmloop_mult_spinbox,
                         self.backend.ao_ttmloop_mult, mult=d)

    @Slot(float)
    def on_ttmloop_limit_spinbox_valueChanged(self, d: float) -> None:
        self.action_send(self.ui.ttmloop_limit_spinbox,
                         self.backend.ao_ttmloop_limit, limit=d)

    @Slot(bool)
    def on_ttmloop_zero_button_clicked(self, checked: bool) -> None:
        self.action_send(self.ui.ttmloop_zero_button,
                         self.backend.ao_ttmloop_zero)

    # Wavefront Sensor

    @Slot(int)
    def on_wfs_emgain_spinbox_valueChanged(self, i: int) -> None:
        self.action_send(self.ui.wfs_emgain_spinbox, self.backend.wfs_emgain,
                         emgain=i)

    @Slot(float)
    def on_wfs_exposuretime_spinbox_valueChanged(self, d: float) -> None:
        self.action_send(self.ui.wfs_exposuretime_spinbox,
                         self.backend.wfs_exposuretime, exposuretime=d)

    @Slot(int)
    def on_wfs_autogain_checkbox_stateChanged(self,
                                              state: Qt.CheckState) -> None:
        self.action_send(self.ui.wfs_autogain_checkbox,
                         self.backend.wfs_autogain_on,
                         state=Qt.CheckState(state) == Qt.CheckState.Checked)

    @Slot(int)
    def on_wfs_autogain_setting_combobox_currentIndexChanged(self, index: int
                                                             ) -> None:
        self.action_send(self.ui.wfs_autogain_setting_combobox,
                         self.backend.wfs_autogain_setting, setting=index)

    @Slot(bool)
    def on_wfs_emgainoff_button_clicked(self, checked: bool) -> None:
        self.action_send([
            self.ui.wfs_emgain_spinbox, self.ui.wfs_autogain_checkbox,
            self.ui.wfs_autogain_setting_combobox, self.ui.wfs_emgainoff_button
        ], self.backend.wfs_emgainoff)

    # Deformable Mirror

    @Slot(float)
    def on_dm_maxstroke_spinbox_valueChanged(self, d: float) -> None:
        self.action_send(self.ui.dm_maxstroke_spinbox,
                         self.backend.dm_maxstroke, stroke=d / 100)

    @Slot(int)
    def on_dm_strokemode_combobox_currentIndexChanged(self,
                                                      index: int) -> None:
        self.action_send(self.ui.dm_strokemode_combobox,
                         self.backend.dm_strokemode, mode=index)

    @Slot(float)
    def on_dm_targetstroke_spinbox_valueChanged(self, d: float) -> None:
        self.action_send(self.ui.dm_targetstroke_spinbox,
                         self.backend.dm_targetstroke, target=d / 100)

    # Observation

    @Slot(int)
    def on_adc_synchronisation_checkbox_stateChanged(self, state: Qt.CheckState
                                                     ) -> None:
        self.action_send(self.ui.adc_synchronisation_checkbox,
                         self.backend.adc_synchronisation,
                         state=Qt.CheckState(state) == Qt.CheckState.Checked)

    @Slot(int)
    def on_ttm_offloading_checkbox_stateChanged(self,
                                                state: Qt.CheckState) -> None:
        self.action_send(self.ui.ttm_offloading_checkbox,
                         self.backend.ttm_offloading,
                         state=Qt.CheckState(state) == Qt.CheckState.Checked)

    # Modal gains

    def on_modalgains_pressed(self, point: QPointF) -> None:
        points = self.modalgains_series.points()
        chart = self.ui.modalgains_plot.chart()

        p, i = chart.find_closest_point(point, points)

        chart.current_dragged_series = self.modalgains_series
        chart.current_dragged_point = p
        chart.current_dragged_index = i

        self.hovered.emit(f'Mode: {p.x():.0f}, Gain: {p.y():.2f}')

    def on_modalgains_released(self, point: QPointF) -> None:
        chart = self.ui.modalgains_plot.chart()

        chart.current_dragged_series = None
        chart.current_dragged_point = None
        chart.current_dragged_index = None

        self.hovered.emit('')

        modalgains = []
        for point in self.modalgains_series.points():
            modalgains.append(point.y())

        self.action_send([], self.backend.ao_dmloop_modalgains,
                         modalgains=modalgains)

    def hover_xy_to_str_modalgains(self, series: QLineSeries, x: float,
                                   y: float) -> None:
        if not np.isnan(x) and not np.isnan(y):
            if series is None:
                self.hovered.emit(f'Mode: {x:.1f}, Gain: {y:.2f}')
            else:
                self.hovered.emit(f'Mode: {x:.0f}, Gain: {y:.2f}')
        else:
            self.hovered.emit('')

    def hover_xy_to_str_modes_coeffs(self, series: QLineSeries, x: float,
                                     y: float) -> None:
        if not np.isnan(x) and not np.isnan(y):
            self.hovered.emit(f'Mode: {x:.1f}, Coefficient: {y:.2f}')
        else:
            self.hovered.emit('')

    @Slot(int)
    def on_cutoff_spinbox_valueChanged(self, i: int) -> None:
        self.ui.last_spinbox.setMinimum(i)
        self.compute_modalgains()

    @Slot(int)
    def on_last_spinbox_valueChanged(self, i: int) -> None:
        self.ui.cutoff_spinbox.setMaximum(i)
        self.compute_modalgains()

    @Slot(int)
    def on_law_combobox_currentIndexChanged(self, index: int) -> None:
        self.compute_modalgains()

    def compute_modalgains(self):
        cutoff = self.ui.cutoff_spinbox.value() - 1
        last = self.ui.last_spinbox.value() - 1
        law = laws[self.ui.law_combobox.currentText()]

        modalgains = np.ones(self.modalgains_series.count())
        modalgains[cutoff:last + 1] = law(cutoff, last + 1)
        modalgains[last + 1:] = 0

        self.display_modalgains(modalgains)

        self.action_send([], self.backend.ao_dmloop_modalgains,
                         modalgains=modalgains)

    def display_modalgains(self, modalgains: np.ndarray[float]) -> None:
        points = []
        for i in range(modalgains.size):
            points.append(QPointF(i + 1, modalgains[i]))

        self.modalgains_series.replace(points)
        self.modalgains_axis_x.setRange(0, modalgains.size + 1)

    def display_modes_coeff(self, modes_coeff: np.ndarray) -> None:
        brush = QBrush(Color.BLUE, Qt.BrushStyle.SolidPattern)

        set = QBarSet('Mode Coefficients')
        set.setBrush(brush)

        # Add zero coeff. to shift the graph
        set.append(0)

        for i in range(modes_coeff.size):
            set.append(modes_coeff[i])

        self.modes_series.clear()
        self.modes_series.append(set)

        series_min = modes_coeff.min()
        series_max = modes_coeff.max()

        abs_max = max(abs(series_min), abs(series_max))

        if abs_max < config.epsilon:
            series_min = -0.01
            series_max = 0.01
        else:
            series_min = -abs_max * 1.05
            series_max = abs_max * 1.05

        self.modes_axis_x.setRange(0, modes_coeff.size + 1)
        self.modes_axis_y.setRange(series_min, series_max)
        self.modes_axis_y.applyNiceNumbers()
