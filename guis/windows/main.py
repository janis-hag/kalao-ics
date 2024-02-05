import time
from datetime import datetime

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QTabWidget

from guis.utils.definitions import Color
from guis.utils.mixins import BackendDataMixin
from guis.utils.widgets import KDetachedTabWindow, KLabel, KMainWindow
from guis.widgets.engineering import EngineeringWidget
from guis.widgets.logs import LogsWidget
from guis.widgets.loop_controls import LoopControlsWidget
from guis.widgets.main import MainWidget
from guis.widgets.monitoring import MonitoringWidget
from guis.widgets.plots import PlotsWidget


class MainWindow(KMainWindow, BackendDataMixin):
    previous_update_time = 0
    fps = 0

    def __init__(self, backend, streams_timer, expert_mode=False,
                 on_sky_unit=False, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.streams_timer = streams_timer

        #self.showMaximized()
        self.resize(1500, 1000)

        self.tabwidget = QTabWidget(parent=self)
        self.setCentralWidget(self.tabwidget)

        self.main = MainWidget(backend, streams_timer, on_sky_unit=on_sky_unit,
                               parent=self)
        self.loop_controls = LoopControlsWidget(backend, parent=self)
        self.monitoring = MonitoringWidget(backend, parent=self)
        self.engineering = EngineeringWidget(backend, parent=self)
        self.plots = PlotsWidget(backend, parent=self)
        self.logs = LogsWidget(backend, parent=self)

        self.widgets = [
            self.main, self.loop_controls, self.monitoring, self.plots,
            self.engineering, self.logs
        ]

        for widget in self.widgets:
            self.tabwidget.addTab(
                widget,
                widget.windowTitle().removesuffix(" - KalAO"))

        self.fps_label = KLabel("Streams refresh rate : {fps:04.1f} FPS |",
                                parent=self)
        self.statusBar().addPermanentWidget(self.fps_label)

        self.last_update_label = KLabel(parent=self)
        self.statusBar().addPermanentWidget(self.last_update_label)

        self.expert_checkbox = QCheckBox('Expert Mode', parent=self)
        self.expert_checkbox.stateChanged.connect(
            self.on_expert_checkbox_stateChanged)
        self.expert_checkbox.setChecked(expert_mode)
        self.statusBar().addPermanentWidget(self.expert_checkbox)
        self.on_expert_checkbox_stateChanged(self.expert_checkbox.checkState())

        for widget in [
                self.main.wfs, self.main.fli, self.main.slopes, self.main.flux,
                self.main.dm, self.loop_controls, self.monitoring,
                self.engineering, self.plots
        ]:
            widget.hovered.connect(self.info_to_statusbar)

        self.initial_tab_color = self.tabwidget.tabBar().tabTextColor(0)

        self.monitoring.updated.connect(self.on_monitoring_updated)
        self.logs.logged.connect(self.on_logs_logged)

        backend.streams_all_updated.connect(self.streams_all_updated)
        backend.all_updated.connect(self.all_updated)

        self.tabwidget.currentChanged.connect(self.on_tabwidget_currentChanged)
        self.tabwidget.tabBarDoubleClicked.connect(
            self.on_tabwidget_tabBarDoubleClicked)

        self.tabwidget.setCurrentIndex(0)

        self.show()
        self.center()

    def on_monitoring_updated(self, outdated, warnings, errors):
        list = []
        color = self.initial_tab_color
        text = self.monitoring.windowTitle().removesuffix(" - KalAO")

        if outdated != 0:
            list.append(f'O: {outdated}')

        if warnings != 0:
            color = Color.ORANGE
            list.append(f'W: {warnings}')

        if errors != 0:
            color = Color.RED
            list.append(f'E: {errors}')

        if len(list) > 0:
            text += f' ({", ".join(list)})'

        tab_index = self.tabwidget.indexOf(self.monitoring)
        self.tabwidget.tabBar().setTabText(tab_index, text)
        self.tabwidget.tabBar().setTabTextColor(tab_index, color)

    def on_logs_logged(self, warnings, errors):
        list = []
        color = self.initial_tab_color
        text = self.logs.windowTitle().removesuffix(" - KalAO")

        if warnings != 0:
            color = Color.ORANGE
            list.append(f'W: {warnings}')

        if errors != 0:
            color = Color.RED
            list.append(f'E: {errors}')

        if len(list) > 0:
            text += f' ({", ".join(list)})'

        tab_index = self.tabwidget.indexOf(self.logs)
        self.tabwidget.tabBar().setTabText(tab_index, text)
        self.tabwidget.tabBar().setTabTextColor(tab_index, color)

    def on_tabwidget_currentChanged(self, i):
        # Logs tab
        if i == self.tabwidget.indexOf(self.logs):
            self.logs.reset_scrollbars()

    def on_tabwidget_tabBarDoubleClicked(self, i):
        if i == 0:
            return

        KDetachedTabWindow(self.tabwidget.widget(i), parent=self)

    def on_expert_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.engineering.setEnabled(True)
            self.loop_controls.setEnabled(True)
        else:
            self.engineering.setEnabled(False)
            self.loop_controls.setEnabled(False)

    def streams_all_updated(self, data):
        now = time.monotonic()

        self.fps = 0.9 * self.fps + 0.1 / (now - self.previous_update_time)

        self.fps_label.updateText(fps=self.fps)

        self.previous_update_time = now

    def all_updated(self, data):
        self.last_update_label.setText(
            'Last update: ' + datetime.now().strftime('%H:%M:%S %d-%m-%Y'))

    def closeEvent(self, event):
        app = QApplication.instance()
        app.quit()

        event.accept()
