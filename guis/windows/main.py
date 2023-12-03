import time

from PySide6.QtCore import Slot
from PySide6.QtGui import Qt

from guis.kalao.definitions import Color, Logo
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOLabel, KalAOMainWindow
from guis.windows.dm import DMWidget
from guis.windows.engineering import EngineeringWidget
from guis.windows.fli import FLIWidget
from guis.windows.flux import FluxWidget
from guis.windows.logs import LogsWidget
from guis.windows.loop_controls import LoopControlsWidget
from guis.windows.plots import PlotsWidget
from guis.windows.slopes import SlopesWidget
from guis.windows.ttm import TTMWidget
from guis.windows.wfs import WFSWidget


class MainWindow(KalAOMainWindow):
    previous_update_time = 0

    TAB_MAIN = 0
    TAB_LOOP = 1
    TAB_PLOTS = 2
    TAB_ENGINEERING = 3
    TAB_LOGS = 4

    def __init__(self, backends, backend, timer_images, parent=None):
        super().__init__(parent)

        self.backends = backends
        self.backend = backend
        self.timer_images = timer_images

        loadUi('main.ui', self)

        #self.showMaximized()

        self.move(100, 0)
        self.resize(1200, 1050)
        self.show()

        self.logo_label.load(str(Logo.svg))
        self.logo_label.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        self.fps_label = KalAOLabel(
            "Streams refresh rate : {fps:.1f} FPS | Data gathering: {duration:.3f} s"
        )
        self.statusBar().addPermanentWidget(self.fps_label)

        self.wfs = WFSWidget(backend, parent=self)
        self.fli = FLIWidget(backend, parent=self)
        self.slopes = SlopesWidget(backend, parent=self)
        self.flux = FluxWidget(backend, parent=self)
        self.dm = DMWidget(backend, parent=self)
        self.ttm = TTMWidget(backend, parent=self)
        self.loop_controls = LoopControlsWidget(backend, parent=self)
        self.engineering = EngineeringWidget(backend, parent=self)
        self.plots = PlotsWidget(backend, parent=self)
        self.logs = LogsWidget(backends, parent=self)

        self.wfs_frame.layout().addWidget(self.wfs)
        self.fli_frame.layout().addWidget(self.fli)
        self.dm_frame.layout().addWidget(self.dm)
        self.slopes_frame.layout().addWidget(self.slopes)
        self.flux_frame.layout().addWidget(self.flux)
        self.ttm_frame.layout().addWidget(self.ttm)

        self.loop_tab.layout().addWidget(self.loop_controls)

        self.engineering_tab.layout().addWidget(self.engineering)

        self.plots_tab.layout().addWidget(self.plots)

        self.logs_tab.layout().addWidget(self.logs)

        for widget in [self.fli, self.slopes, self.dm, self.ttm]:
            self.onsky_checkbox.stateChanged.connect(widget.change_units)
            widget.change_units(self.onsky_checkbox.checkState())

        for widget in [self.wfs, self.fli, self.slopes, self.flux, self.dm]:
            self.colormap_checkbox.stateChanged.connect(widget.change_colormap)
            widget.change_colormap(self.colormap_checkbox.checkState())

        self.wfs.hovered.connect(self.info_point)
        self.fli.hovered.connect(self.info_point)
        self.slopes.hovered.connect(self.info_point)
        self.flux.hovered.connect(self.info_point)
        self.dm.hovered.connect(self.info_point)
        self.plots.hovered.connect(self.info_point)

        self.on_tabwidget_currentChanged(self.tabwidget.currentIndex())

        self.logs_initial_tab_color = self.tabwidget.tabBar().tabTextColor(
            self.TAB_LOGS)
        self.logs.logged.connect(self.on_logs_logged)

        self.tabwidget.setCurrentIndex(self.TAB_MAIN)

        backend.streams_updated.connect(self.data_updated)

    def on_logs_logged(self, errors, warnings):
        list = []
        color = self.logs_initial_tab_color
        text = 'Logs'

        if warnings != 0:
            color = Color.ORANGE
            list.append(f'W: {warnings}')

        if errors != 0:
            color = Color.RED
            list.append(f'E: {errors}')

        if len(list) > 0:
            text += f' ({", ".join(list)})'

        self.tabwidget.tabBar().setTabText(self.TAB_LOGS, text)
        self.tabwidget.tabBar().setTabTextColor(self.TAB_LOGS, color)

    @Slot(int)
    def on_freeze_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.timer_images.stop()
            self.fps_label.setText('')
        else:
            self.timer_images.start()

    def info_point(self, string):
        if string:
            self.statusbar.showMessage(string)
        else:
            self.statusbar.clearMessage()

    @Slot(int)
    def on_tabwidget_currentChanged(self, i):
        # Main tab
        if i == self.TAB_MAIN:
            self.timer_images.start()

        # Logs tab
        elif i == self.TAB_LOGS:
            self.logs.reset_scrollbars()

        if i != self.TAB_MAIN:
            self.timer_images.stop()
            self.fps_label.setText('')

    def data_updated(self, data):
        now = time.monotonic()

        self.fps_label.updateText(fps=(1 / (now - self.previous_update_time)),
                                  duration=data['metadata']['duration'])

        self.previous_update_time = now
