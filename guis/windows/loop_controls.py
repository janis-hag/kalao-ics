import numpy as np

from PySide6.QtCharts import QLineSeries, QValueAxis
from PySide6.QtCore import QPointF, Qt, Slot

from guis.kalao.mixins import BackendActionMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

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


class LoopControlsWidget(KalAOWidget, BackendActionMixin):
    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('loop_controls.ui', self)
        self.resize(600, 400)

        # Create Chart and set General Chart setting
        chart = self.modalgains_plot.chart

        # X Axis Settings
        self.axisX = QValueAxis()
        self.axisX.setLabelFormat("%.0f")
        self.axisX.setTickAnchor(0)
        self.axisX.setTickInterval(10)
        self.axisX.setTickType(QValueAxis.TicksDynamic)
        self.axisX.setRange(-1, 1)
        chart.addAxis(self.axisX, Qt.AlignBottom)

        # Y Axis Settings
        self.axisY = QValueAxis()
        self.axisY.setTickAnchor(0)
        self.axisY.setTickInterval(0.25)
        self.axisY.setTickType(QValueAxis.TicksDynamic)
        self.axisY.setRange(-0.05, 1.05)
        chart.addAxis(self.axisY, Qt.AlignLeft)

        # Serie
        series = self.modalgains_series = QLineSeries()
        series.setName("Modal gains")
        series.setPointsVisible(True)
        series.pressed.connect(self.on_modalgains_pressed)
        series.released.connect(self.on_modalgains_released)

        chart.addSeries(series)
        series.attachAxis(self.axisX)
        series.attachAxis(self.axisY)

        for s in laws.keys():
            self.law_combobox.addItem(s)

        backend.streams_updated.connect(self.data_updated)

    def data_updated(self, data):
        # DM Loop

        loopON = self.backend.consume_param(data, 'mfilt-1', 'loopON')
        if loopON is not None:
            if loopON == 1:
                self.dm_loop_on_checkbox.setCheckState(Qt.Checked)
            else:
                self.dm_loop_on_checkbox.setCheckState(Qt.Unchecked)

        loopgain = self.backend.consume_param(data, 'mfilt-1', 'loopgain')
        if loopgain is not None:
            self.dm_loop_gain_spinbox.setValue(loopgain)

        loopmult = self.backend.consume_param(data, 'mfilt-1', 'loopmult')
        if loopmult is not None:
            self.dm_loop_mult_spinbox.setValue(loopmult)

        looplimit = self.backend.consume_param(data, 'mfilt-1', 'looplimit')
        if looplimit is not None:
            self.dm_loop_limit_spinbox.setValue(looplimit)

        # TTM Loop

        loopON = self.backend.consume_param(data, 'mfilt-2', 'loopON')
        if loopON is not None:
            if loopON == 1:
                self.ttm_loop_on_checkbox.setCheckState(Qt.Checked)
            else:
                self.ttm_loop_on_checkbox.setCheckState(Qt.Unchecked)

        loopgain = self.backend.consume_param(data, 'mfilt-2', 'loopgain')
        if loopgain is not None:
            self.ttm_loop_gain_spinbox.setValue(loopgain)

        loopmult = self.backend.consume_param(data, 'mfilt-2', 'loopmult')
        if loopmult is not None:
            self.ttm_loop_mult_spinbox.setValue(loopmult)

        looplimit = self.backend.consume_param(data, 'mfilt-2', 'looplimit')
        if looplimit is not None:
            self.ttm_loop_limit_spinbox.setValue(looplimit)

        # Modal gains

        img = self.backend.consume_stream(data, 'aol1_mgainfact')

        if img is not None:
            self.display_modalgains(img)

            self.cutoff_spinbox.setMaximum(img.size - 1)
            self.cutoff_spinbox.setValue(img.size - 1)
            self.last_spinbox.setMaximum(img.size - 1)
            self.last_spinbox.setValue(img.size - 1)

    # DM Loop

    @Slot(int)
    def on_dm_loop_on_checkbox_stateChanged(self, state):
        self.action_send(self.dm_loop_on_checkbox, self.backend.set_dm_loop_on,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(float)
    def on_dm_loop_gain_spinbox_valueChanged(self, d):
        self.action_send(self.dm_loop_gain_spinbox,
                         self.backend.set_dm_loop_gain, d)

    @Slot(float)
    def on_dm_loop_mult_spinbox_valueChanged(self, d):
        self.action_send(self.dm_loop_mult_spinbox,
                         self.backend.set_dm_loop_mult, d)

    @Slot(float)
    def on_dm_loop_limit_spinbox_valueChanged(self, d):
        self.action_send(self.dm_loop_limit_spinbox,
                         self.backend.set_dm_loop_limit, d)

    # TTM Loop

    @Slot(int)
    def on_ttm_loop_on_checkbox_stateChanged(self, state):
        self.action_send(self.ttm_loop_on_checkbox,
                         self.backend.set_ttm_loop_on,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(float)
    def on_ttm_loop_gain_spinbox_valueChanged(self, d):
        self.action_send(self.ttm_loop_gain_spinbox,
                         self.backend.set_ttm_loop_gain, d)

    @Slot(float)
    def on_ttm_loop_mult_spinbox_valueChanged(self, d):
        self.action_send(self.ttm_loop_mult_spinbox,
                         self.backend.set_ttm_loop_mult, d)

    @Slot(float)
    def on_ttm_loop_limit_spinbox_valueChanged(self, d):
        self.action_send(self.ttm_loop_limit_spinbox,
                         self.backend.set_ttm_loop_limit, d)

    # Modal gains

    def on_modalgains_pressed(self, point):
        points = self.modalgains_series.points()

        p = min(points, key=lambda x: abs((x - point).x()))
        i = points.index(p)

        self.modalgains_plot.chart.current_series = self.modalgains_series
        self.modalgains_plot.chart.current_point = p
        self.modalgains_plot.chart.current_index = i

    def on_modalgains_released(self, point):
        self.modalgains_plot.chart.current_series = None
        self.modalgains_plot.chart.current_point = None
        self.modalgains_plot.chart.current_index = None

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

    def display_modalgains(self, modalgains):
        self.modalgains_series.removePoints(0, self.modalgains_series.count())

        for i in range(modalgains.size):
            self.modalgains_series.append(QPointF(i, modalgains[i]))

        self.axisX.setRange(-1, modalgains.size)
