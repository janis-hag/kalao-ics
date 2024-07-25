from datetime import datetime

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QTabWidget

from guis.utils.definitions import Color
from guis.utils.mixins import BackendDataMixin
from guis.utils.widgets import KDetachedTabWindow, KLabel, KMainWindow
from guis.widgets.engineering import EngineeringWidget
from guis.widgets.help import HelpWidget
from guis.widgets.logs import LogsWidget
from guis.widgets.loop_controls import LoopControlsWidget
from guis.widgets.main import MainWidget
from guis.widgets.monitoring import MonitoringWidget
from guis.widgets.plots import PlotsWidget


class MainWindow(KMainWindow, BackendDataMixin):
    def __init__(self, backend, expert_mode=False, on_sky_unit=False,
                 deadman=False, parent=None):
        super().__init__(parent)

        self.backend = backend

        #self.showMaximized()
        self.resize(1700, 1000)

        self.tabwidget = QTabWidget(parent=self)
        self.setCentralWidget(self.tabwidget)

        self.main = MainWidget(backend, on_sky_unit=on_sky_unit, parent=self)
        self.loop_controls = LoopControlsWidget(backend, parent=self)
        self.monitoring = MonitoringWidget(backend, parent=self)
        self.engineering = EngineeringWidget(backend, deadman=deadman,
                                             parent=self)
        self.plots = PlotsWidget(backend, parent=self)
        self.logs = LogsWidget(backend, parent=self)
        self.help = HelpWidget(parent=self)

        self.widgets = [
            self.main, self.loop_controls, self.monitoring, self.plots,
            self.engineering, self.logs, self.help
        ]

        for widget in self.widgets:
            self.tabwidget.addTab(
                widget,
                widget.windowTitle().removesuffix(' - KalAO'))

        self.last_update_label = KLabel(parent=self)
        self.statusBar().addPermanentWidget(self.last_update_label)

        self.expert_checkbox = QCheckBox('Expert Mode', parent=self)
        self.expert_checkbox.setChecked(
            True
        )  # Default layout correspond to checked state, needed for next call to work properly
        self.expert_checkbox.stateChanged.connect(
            self.on_expert_checkbox_stateChanged)
        self.statusBar().addPermanentWidget(self.expert_checkbox)

        for widget in [
                self.main, self.main.wfs, self.main.camera, self.main.slopes,
                self.main.flux, self.main.dm, self.main.ttm,
                self.loop_controls, self.monitoring, self.engineering,
                self.plots
        ]:
            widget.hovered.connect(self.info_to_statusbar)

        self.initial_tab_color = self.tabwidget.tabBar().tabTextColor(0)

        self.monitoring.updated.connect(self.on_monitoring_updated)
        self.engineering.updated.connect(self.on_engineering_updated)
        self.logs.logged.connect(self.on_logs_logged)

        backend.all_updated.connect(self.all_updated)

        self.tabwidget.currentChanged.connect(self.on_tabwidget_currentChanged)
        self.tabwidget.tabBarDoubleClicked.connect(
            self.on_tabwidget_tabBarDoubleClicked)

        self.tabwidget.setCurrentIndex(0)

        self.expert_checkbox.setChecked(expert_mode)

        self.show()
        self.center()

    def on_monitoring_updated(self, outdated, warnings, alarms):
        list = []
        color = self.initial_tab_color
        text = self.monitoring.windowTitle().removesuffix(' - KalAO')

        if outdated != 0:
            list.append(f'O: {outdated}')

        if warnings != 0:
            color = Color.ORANGE
            list.append(f'W: {warnings}')

        if alarms != 0:
            color = Color.RED
            list.append(f'A: {alarms}')

        if len(list) > 0:
            text += f' ({", ".join(list)})'

        tab_index = self.tabwidget.indexOf(self.monitoring)
        self.tabwidget.tabBar().setTabText(tab_index, text)
        self.tabwidget.tabBar().setTabTextColor(tab_index, color)

    def on_engineering_updated(self, warnings, errors):
        list = []
        color = self.initial_tab_color
        text = self.engineering.windowTitle().removesuffix(' - KalAO')

        if warnings != 0:
            color = Color.ORANGE
            list.append(f'W: {warnings}')

        if errors != 0:
            color = Color.RED
            list.append(f'E: {errors}')

        if len(list) > 0:
            text += f' ({", ".join(list)})'

        tab_index = self.tabwidget.indexOf(self.engineering)
        self.tabwidget.tabBar().setTabText(tab_index, text)
        self.tabwidget.tabBar().setTabTextColor(tab_index, color)

    def on_logs_logged(self, warnings, errors):
        list = []
        color = self.initial_tab_color
        text = self.logs.windowTitle().removesuffix(' - KalAO')

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

    def all_updated(self, data):
        self.last_update_label.setText(
            'Last update: ' +
            datetime.now().astimezone().strftime('%H:%M:%S %d-%m-%Y'))

    def closeEvent(self, event):
        app = QApplication.instance()
        app.quit()

        event.accept()
