import time

import numpy as np

from PySide2.QtGui import Qt
from PySide2.QtWidgets import QCheckBox

from guis.kalao.definitions import Color, Logo
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOLabel, KalAOMainWindow
from guis.windows.dm import DMWidget
from guis.windows.dm_channels import DMChannelsWindow
from guis.windows.fli import FLIWidget
from guis.windows.flux import FluxWidget
from guis.windows.logs import LogsWidget
from guis.windows.plots import PlotsWidget
from guis.windows.slopes import SlopesWidget
from guis.windows.ttm import TTMWidget
from guis.windows.wfs import WFSWidget


class MainWindow(KalAOMainWindow):
    previous_update_time = 0

    TAB_MAIN = 0
    TAB_PLOTS = 1
    TAB_ENGINEERING = 2
    TAB_LOGS = 3

    def __init__(self, backend, timer_images, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.timer_images = timer_images

        loadUi('main.ui', self)

        #self.showMaximized()

        self.move(100, 0)
        self.resize(1200, 1050)
        self.show()

        self.logo_label.load(str(Logo.svg))
        self.logo_label.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        checkbox = QCheckBox("DM Loop ON")
        self.statusBar().addPermanentWidget(checkbox)

        checkbox = QCheckBox("TTM Loop ON")
        self.statusBar().addPermanentWidget(checkbox)

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
        self.plots = PlotsWidget(backend, parent=self)
        self.logs = LogsWidget(backend, parent=self)

        self.wfs_frame.layout().addWidget(self.wfs)
        self.fli_frame.layout().addWidget(self.fli)
        self.dm_frame.layout().addWidget(self.dm)
        self.slopes_frame.layout().addWidget(self.slopes)
        self.flux_frame.layout().addWidget(self.flux)
        self.ttm_frame.layout().addWidget(self.ttm)

        self.plots_tab.layout().addWidget(self.plots)

        self.logs_tab.layout().addWidget(self.logs)

        for widget in [self.fli, self.slopes, self.dm, self.ttm]:
            self.onsky_checkbox.stateChanged.connect(widget.change_units)
            widget.change_units(self.onsky_checkbox.checkState())

        for widget in [self.wfs, self.fli, self.slopes, self.flux, self.dm]:
            self.colormap_checkbox.stateChanged.connect(widget.change_colormap)
            widget.change_colormap(self.colormap_checkbox.checkState())

        self.freeze_checkbox.stateChanged.connect(self.freeze_checkbox_changed)

        self.wfs.hovered.connect(self.info_point)
        self.fli.hovered.connect(self.info_point)
        self.slopes.hovered.connect(self.info_point)
        self.flux.hovered.connect(self.info_point)
        self.dm.hovered.connect(self.info_point)

        self.tabwidget.currentChanged.connect(self.tab_changed)
        self.tab_changed(self.tabwidget.currentIndex())

        self.logs.logged.connect(self.logs_error)
        self.logs_tab_color = self.tabwidget.tabBar().tabTextColor(
            self.TAB_LOGS)

        self.dm_window_button.clicked.connect(self.open_dm_window)
        self.ttm_window_button.clicked.connect(self.open_ttm_window)

        backend.updated.connect(self.data_updated)

    def logs_error(self, errors, warnings):
        list = []
        color = self.logs_tab_color
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

    def freeze_checkbox_changed(self, state):
        if state == Qt.Checked:
            self.timer_images.stop()
            self.fps_label.updateText(fps=np.nan, duration=np.nan)
        else:
            self.timer_images.start()

    def info_point(self, string):
        if string:
            self.statusbar.showMessage(string)
        else:
            self.statusbar.clearMessage()

    def tab_changed(self, i):
        # Main tab
        if i == self.TAB_MAIN:
            self.timer_images.start()

        # Logs tab
        elif i == self.TAB_LOGS:
            self.logs.reset_scrollbars()

        if i != self.TAB_MAIN:
            self.timer_images.stop()
            self.fps_label.updateText(fps=np.nan, duration=np.nan)

    def data_updated(self):
        now = time.monotonic()

        self.fps_label.updateText(fps=(1 / (now - self.previous_update_time)),
                                  duration=self.backend.data['duration'])

        self.previous_update_time = now

    def open_dm_window(self, checked):
        self.dm_channels = DMChannelsWindow(1)

    def open_ttm_window(self, checked):
        self.ttm_channels = DMChannelsWindow(2)
