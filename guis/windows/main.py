import time

import numpy as np

from PySide6.QtCore import Slot
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QApplication, QCheckBox

from guis.kalao.definitions import Color, Logo
from guis.kalao.mixins import BackendDataMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOLabel, KalAOMainWindow
from guis.windows.dm import DMWidget
from guis.windows.engineering import EngineeringWidget
from guis.windows.fli import FLIWidget
from guis.windows.flux import FluxWidget
from guis.windows.logs import LogsWidget
from guis.windows.loop_controls import LoopControlsWidget
from guis.windows.monitoring import MonitoringWidget
from guis.windows.plots import PlotsWidget
from guis.windows.slopes import SlopesWidget
from guis.windows.ttm import TTMWidget
from guis.windows.wfs import WFSWidget

import config


class MainWindow(KalAOMainWindow, BackendDataMixin):
    previous_update_time = 0

    TAB_MAIN = 0
    TAB_LOOP = 1
    TAB_MONITORING = 3
    TAB_PLOTS = 3
    TAB_ENGINEERING = 4
    TAB_LOGS = 5

    def __init__(self, backends, backend, timer_streams, expert_mode=False,
                 on_sky_unit=False, parent=None):
        super().__init__(parent)

        self.backends = backends
        self.backend = backend
        self.timer_streams = timer_streams

        loadUi('main.ui', self)

        #self.showMaximized()

        self.move(100, 0)
        self.resize(1300, 900)
        self.show()

        self.logo_label.load(str(Logo.svg))
        self.logo_label.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        self.fps_label = KalAOLabel(
            "Streams refresh rate : {fps:.1f} FPS | Data gathering: {duration:.3f} s"
        )
        self.statusBar().addPermanentWidget(self.fps_label)

        self.expert_checkbox = QCheckBox('Expert Mode')
        self.expert_checkbox.setChecked(expert_mode)
        self.expert_checkbox.stateChanged.connect(
            self.on_expert_checkbox_stateChanged)
        self.statusBar().addPermanentWidget(self.expert_checkbox)

        self.fli_remaining_time_lineedit.updateText(remaining_time=np.nan)
        self.fli_exposure_time_lineedit.updateText(exposure_time=np.nan)
        self.fli_ccd_temperature_lineedit.updateText(ccd_temperature=np.nan)
        self.nuvu_emgain_lineedit.updateText(emgain=np.nan)
        self.nuvu_exposuretime_lineedit.updateText(exposuretime=np.nan)
        self.nuvu_framerate_lineedit.updateText(framerate=np.nan)
        self.nuvu_ccd_temperature_lineedit.updateText(ccd_temperature=np.nan)

        self.wfs = WFSWidget(backend, parent=self)
        self.fli = FLIWidget(backend, parent=self)
        self.slopes = SlopesWidget(backend, parent=self)
        self.flux = FluxWidget(backend, parent=self)
        self.dm = DMWidget(backend, parent=self)
        self.ttm = TTMWidget(backend, parent=self)
        self.loop_controls = LoopControlsWidget(backend, parent=self)
        self.monitoring = MonitoringWidget(backend, parent=self)
        self.engineering = EngineeringWidget(backend, parent=self)
        self.plots = PlotsWidget(backend, parent=self)
        self.logs = LogsWidget(backend, parent=self)

        self.wfs_frame.layout().addWidget(self.wfs)
        self.fli_frame.layout().addWidget(self.fli)
        self.dm_frame.layout().addWidget(self.dm)
        self.slopes_frame.layout().addWidget(self.slopes)
        self.flux_frame.layout().addWidget(self.flux)
        self.ttm_frame.layout().addWidget(self.ttm)

        self.loop_tab.layout().addWidget(self.loop_controls)
        self.monitoring_tab.layout().addWidget(self.monitoring)
        self.engineering_tab.layout().addWidget(self.engineering)
        self.plots_tab.layout().addWidget(self.plots)
        self.logs_tab.layout().addWidget(self.logs)

        for widget in [self.fli, self.slopes, self.dm, self.ttm]:
            self.onsky_checkbox.stateChanged.connect(widget.change_units)
            widget.change_units(self.onsky_checkbox.checkState())

        for widget in [self.wfs, self.fli, self.slopes, self.flux, self.dm]:
            self.colormap_checkbox.stateChanged.connect(widget.change_colormap)
            widget.change_colormap(self.colormap_checkbox.checkState())

        self.wfs.hovered.connect(self.info_to_statusbar)
        self.fli.hovered.connect(self.info_to_statusbar)
        self.slopes.hovered.connect(self.info_to_statusbar)
        self.flux.hovered.connect(self.info_to_statusbar)
        self.dm.hovered.connect(self.info_to_statusbar)
        self.plots.hovered.connect(self.info_to_statusbar)
        self.loop_controls.hovered.connect(self.info_to_statusbar)

        self.logs_initial_tab_color = self.tabwidget.tabBar().tabTextColor(
            self.TAB_LOGS)
        self.logs.logged.connect(self.on_logs_logged)

        self.tabwidget.setCurrentIndex(self.TAB_MAIN)
        self.on_expert_checkbox_stateChanged(self.expert_checkbox.checkState())

        backend.streams_updated.connect(self.streams_updated)
        backend.data_updated.connect(self.data_updated)

        self.on_tabwidget_currentChanged(self.tabwidget.currentIndex())

        self.onsky_checkbox.setChecked(on_sky_unit)

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
            self.timer_streams.stop()
            self.fps_label.setText('')
        else:
            self.timer_streams.start()

    @Slot(int)
    def on_tabwidget_currentChanged(self, i):
        # Main tab
        if i == self.TAB_MAIN:
            self.timer_streams.start()

        # Logs tab
        elif i == self.TAB_LOGS:
            self.logs.reset_scrollbars()

        if i != self.TAB_MAIN:
            self.timer_streams.stop()
            self.fps_label.setText('')

    def on_expert_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.engineering.setEnabled(True)
            self.loop_controls.setEnabled(True)
        else:
            self.engineering.setEnabled(False)
            self.loop_controls.setEnabled(False)

    def streams_updated(self, data):
        now = time.monotonic()

        self.fps_label.updateText(fps=(1 / (now - self.previous_update_time)),
                                  duration=data['metadata']['duration'])

        self.previous_update_time = now

    def data_updated(self, data):
        ### AO

        loopON = self.consume_param(data, 'mfilt-1', 'loopON')
        if loopON is not None:
            if loopON == 1:
                self.dm_loop_indicator.setStatus(Color.GREEN, loopON)
            else:
                self.dm_loop_indicator.setStatus(Color.RED, loopON)

        loopON = self.consume_param(data, 'mfilt-2', 'loopON')
        if loopON is not None:
            if loopON == 1:
                self.ttm_loop_indicator.setStatus(Color.GREEN, loopON)
            else:
                self.ttm_loop_indicator.setStatus(Color.RED, loopON)

        ### FLI

        exposure_time = self.consume_dict(data, 'fli', 'exposure_time')
        if exposure_time is not None:
            self.fli_exposure_time_lineedit.updateText(
                exposure_time=exposure_time)

        remaining_time = self.consume_dict(data, 'fli', 'remaining_time')
        if remaining_time is not None:
            if remaining_time >= 0.001:
                self.fli_exposure_indicator.setStatus(Color.GREEN,
                                                      remaining_time)
            else:
                self.fli_exposure_indicator.setStatus(
                    Color.RED, remaining_time)  #TODO: remaining_time if -1 ?

            self.fli_remaining_time_lineedit.updateText(
                remaining_time=remaining_time)

        ccd = self.consume_dict(data, 'fli', 'ccd')
        if ccd is not None:
            self.fli_ccd_temperature_lineedit.updateText(ccd_temperature=ccd)

        ### Nuvu

        autogain_on = self.consume_param(data, config.FPS.NUVU, 'autogain_on')
        if autogain_on is not None:
            if autogain_on == 1:
                self.nuvu_autogain_indicator.setStatus(Color.GREEN,
                                                       autogain_on)
            else:
                self.nuvu_autogain_indicator.setStatus(Color.RED, autogain_on)

        nuvu_emgain = self.consume_stream_keyword(data, config.Streams.NUVU,
                                                  'EMGAIN')
        if nuvu_emgain is not None:
            self.nuvu_emgain_lineedit.updateText(emgain=nuvu_emgain)

        nuvu_exposuretime = self.consume_stream_keyword(
            data, config.Streams.NUVU, 'EXPTIME')
        if nuvu_exposuretime is not None:
            self.nuvu_exposuretime_lineedit.updateText(
                exposuretime=nuvu_exposuretime)

        nuvu_mframerate = self.consume_stream_keyword(data,
                                                      config.Streams.NUVU,
                                                      'MFRATE')
        if nuvu_mframerate is not None:
            self.nuvu_framerate_lineedit.updateText(framerate=nuvu_mframerate)

        nuvu_temp_ccd = self.consume_stream_keyword(data, config.Streams.NUVU,
                                                    'T_CCD')
        if nuvu_temp_ccd is not None:
            self.nuvu_ccd_temperature_lineedit.updateText(
                ccd_temperature=nuvu_temp_ccd)

    def closeEvent(self, event):
        app = QApplication.instance()
        app.quit()

        event.accept()
