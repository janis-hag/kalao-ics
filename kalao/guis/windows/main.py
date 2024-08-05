from datetime import datetime
from typing import Any

from PySide6.QtGui import QCloseEvent, QIcon, Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QTabWidget, QWidget

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.widgets import KLabel, KMainWindow
from kalao.guis.widgets.engineering import EngineeringWidget
from kalao.guis.widgets.help import HelpWidget
from kalao.guis.widgets.logs import LogsWidget
from kalao.guis.widgets.loop_controls import LoopControlsWidget
from kalao.guis.widgets.main import MainWidget
from kalao.guis.widgets.monitoring import MonitoringWidget
from kalao.guis.widgets.plots import PlotsWidget
from kalao.guis.widgets.telemetry import TelemetryWidget


class MainWindow(KMainWindow, BackendDataMixin):
    def __init__(self, backend: AbstractBackend, expert_mode: bool = False,
                 on_sky_unit: bool = False, deadman: bool = False,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend

        #self.showMaximized()
        self.resize(1600, 900)

        self.tabwidget = QTabWidget(parent=self)
        self.setCentralWidget(self.tabwidget)

        self.main = MainWidget(backend, on_sky_unit=on_sky_unit, parent=self)
        self.loop_controls = LoopControlsWidget(backend, parent=self)
        self.telemetry = TelemetryWidget(backend, parent=self)
        self.monitoring = MonitoringWidget(backend, parent=self)
        self.engineering = EngineeringWidget(backend, deadman=deadman,
                                             parent=self)
        self.plots = PlotsWidget(backend, parent=self)
        self.logs = LogsWidget(backend, parent=self)
        self.help = HelpWidget(parent=self)

        self.widgets = [
            self.main,
            self.loop_controls,
            self.telemetry,
            self.monitoring,
            self.plots,
            self.engineering,
            self.logs,
            self.help,
        ]
        self.widgets_icons = [
            ':/assets/icons/go-home.svg',
            ':/assets/icons/settings-configure.svg',
            ':/assets/icons/view-statistics.svg',
            ':/assets/icons/server-database.svg',
            ':/assets/icons/view-media-chart.svg',
            ':/assets/icons/folder-build.svg',
            ':/assets/icons/folder-text.svg',
            ':/assets/icons/help-about.svg',
        ]

        for widget, icon in zip(self.widgets, self.widgets_icons):
            self.tabwidget.addTab(
                widget, QIcon(icon),
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
                self.loop_controls, self.telemetry, self.monitoring,
                self.engineering, self.plots
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

        # Done by __main__ after splash screen end
        # self.show()
        # self.center()

    def on_monitoring_updated(self, outdated: int, warnings: int,
                              alarms: int) -> None:
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

    def on_engineering_updated(self, warnings: int, errors: int) -> None:
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

    def on_logs_logged(self, warnings: int, errors: int) -> None:
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

    def on_tabwidget_currentChanged(self, i: int) -> None:
        # Logs tab
        if i == self.tabwidget.indexOf(self.logs):
            self.logs.reset_scrollbars()

    def on_tabwidget_tabBarDoubleClicked(self, i: int) -> None:
        if i == 0:
            return

        KDetachedTabWindow(self.tabwidget.widget(i), self)

    def on_expert_checkbox_stateChanged(self, state: Qt.CheckState) -> None:
        if Qt.CheckState(state) == Qt.CheckState.Checked:
            self.engineering.setEnabled(True)
            self.loop_controls.setEnabled(True)
        else:
            self.engineering.setEnabled(False)
            self.loop_controls.setEnabled(False)

    def all_updated(self, data: dict[str, Any]) -> None:
        self.last_update_label.setText(
            f'Last update: {datetime.now().astimezone():%H:%M:%S %d-%m-%Y}')

    def closeEvent(self, event: QCloseEvent) -> None:
        app = QApplication.instance()
        app.quit()

        event.accept()


class KDetachedTabWindow(KMainWindow):
    def __init__(self, widget: QWidget, mainwindow: MainWindow, *args:
                 tuple[Any, ...], **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.mainwindow = mainwindow

        self.setWindowTitle(widget.windowTitle())
        self.setCentralWidget(widget)
        self.resize(mainwindow.size())
        self.show()
        self.center()

        if hasattr(widget, 'hovered'):
            self.statusBar().show()
            widget.hovered.disconnect(self.mainwindow.info_to_statusbar)
            widget.hovered.connect(self.info_to_statusbar)

        widget.show()

    def closeEvent(self, event: QCloseEvent) -> None:
        widget = self.centralWidget()

        i = self.mainwindow.widgets.index(widget)
        icon = self.mainwindow.widgets_icons[i]

        while i > 0:
            i -= 1
            j = self.mainwindow.tabwidget.indexOf(self.mainwindow.widgets[i])
            if j != -1:
                self.mainwindow.tabwidget.insertTab(
                    j + 1, widget, QIcon(icon),
                    widget.windowTitle().removesuffix(' - KalAO'))
                self.mainwindow.tabwidget.setCurrentIndex(j + 1)
                break
        else:
            self.mainwindow.tabwidget.addTab(
                widget,
                widget.windowTitle().removesuffix(' - KalAO'))

        if hasattr(widget, 'hovered'):
            widget.hovered.disconnect(self.info_to_statusbar)
            widget.hovered.connect(self.mainwindow.info_to_statusbar)

        return super().closeEvent(event)
