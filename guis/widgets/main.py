import numpy as np

from PySide6.QtCore import Slot
from PySide6.QtGui import Qt

from guis.utils.definitions import Color, Logo
from guis.utils.mixins import BackendDataMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KWidget
from guis.widgets.camera import CameraWidget
from guis.widgets.dm import DMWidget
from guis.widgets.flux import FluxWidget
from guis.widgets.slopes import SlopesWidget
from guis.widgets.ttm import TTMWidget
from guis.widgets.wfs import WFSWidget

import config


class MainWidget(KWidget, BackendDataMixin):
    def __init__(self, backend, streams_timer, on_sky_unit=False, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.streams_timer = streams_timer

        loadUi('main.ui', self)
        self.resize(1300, 900)

        self.logo_label.load(str(Logo.svg))
        self.logo_label.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        self.camera_exposure_time_lineedit.updateText(exposure_time=np.nan)
        self.camera_remaining_time_lineedit.updateText(remaining_time=np.nan)
        self.camera_remaining_frames_lineedit.updateText(
            remaining_frames=np.nan)
        self.camera_ccd_temperature_lineedit.updateText(ccd_temperature=np.nan)
        self.wfs_emgain_lineedit.updateText(emgain=np.nan)
        self.wfs_exposuretime_lineedit.updateText(exposuretime=np.nan)
        self.wfs_framerate_lineedit.updateText(framerate=np.nan)
        self.wfs_ccd_temperature_lineedit.updateText(ccd_temperature=np.nan)

        self.wfs = WFSWidget(backend, parent=self)
        self.fli = CameraWidget(backend, parent=self)
        self.slopes = SlopesWidget(backend, parent=self)
        self.flux = FluxWidget(backend, parent=self)
        self.dm = DMWidget(backend, parent=self)
        self.ttm = TTMWidget(backend, parent=self)

        self.wfs_frame.layout().addWidget(self.wfs)
        self.camera_frame.layout().addWidget(self.fli)
        self.dm_frame.layout().addWidget(self.dm)
        self.slopes_frame.layout().addWidget(self.slopes)
        self.flux_frame.layout().addWidget(self.flux)
        self.ttm_frame.layout().addWidget(self.ttm)

        for widget in [self.fli, self.slopes, self.dm, self.ttm]:
            self.onsky_checkbox.stateChanged.connect(widget.change_units)
            widget.change_units(self.onsky_checkbox.checkState())

        for widget in [self.wfs, self.fli, self.slopes, self.flux, self.dm]:
            self.colormap_checkbox.stateChanged.connect(widget.change_colormap)
            widget.change_colormap(self.colormap_checkbox.checkState())

        self.onsky_checkbox.setChecked(on_sky_unit)

        backend.all_updated.connect(self.all_updated)

    @Slot(int)
    def on_freeze_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.streams_timer.stop()
            #self.fps_label.setText('') #TODO: move to mainwindow
        else:
            self.streams_timer.start()

    def all_updated(self, data):
        ### Instrument

        sequencer_status_v, sequencer_status_t = self.consume_db(
            data, 'obs', 'sequencer_status')
        if sequencer_status_v is not None:
            self.sequencer_lineedit.setText(sequencer_status_v)

        ### AO

        loopON = self.consume_param(data, config.FPS.DMLOOP, 'loopON')
        if loopON is not None:
            if loopON is True:
                self.dmloop_indicator.setStatus(Color.GREEN, loopON)
            elif loopON is False:
                self.dmloop_indicator.setStatus(Color.BLACK, loopON)
            else:
                self.dmloop_indicator.setStatus(Color.RED, loopON)

        loopON = self.consume_param(data, config.FPS.TTMLOOP, 'loopON')
        if loopON is not None:
            if loopON is True:
                self.ttmloop_indicator.setStatus(Color.GREEN, loopON)
            elif loopON is False:
                self.ttmloop_indicator.setStatus(Color.BLACK, loopON)
            else:
                self.ttmloop_indicator.setStatus(Color.RED, loopON)

        ### Camera

        exposure_time = self.consume_dict(data, 'camera', 'exposure_time')
        if exposure_time is not None:
            self.camera_exposure_time_lineedit.updateText(
                exposure_time=exposure_time)

        remaining_time = self.consume_dict(data, 'camera', 'remaining_time')
        if remaining_time is not None:
            self.camera_remaining_time_lineedit.updateText(
                remaining_time=remaining_time)

        remaining_frames = self.consume_dict(data, 'camera',
                                             'remaining_frames')
        if remaining_frames is not None:
            self.camera_remaining_frames_lineedit.updateText(
                remaining_frames=remaining_frames)

            if remaining_frames > 0:
                self.camera_exposure_indicator.setStatus(
                    Color.GREEN, remaining_frames)
            elif remaining_frames == 0:
                self.camera_exposure_indicator.setStatus(
                    Color.BLACK, remaining_frames)
            else:
                self.camera_exposure_indicator.setStatus(
                    Color.RED, remaining_frames)

        ccd = self.consume_dict(data, 'camera', 'ccd')
        if ccd is not None:
            self.camera_ccd_temperature_lineedit.updateText(
                ccd_temperature=ccd)

        ### WFS

        autogain_on = self.consume_param(data, config.FPS.NUVU, 'autogain_on')
        if autogain_on is not None:
            if autogain_on is True:
                self.wfs_autogain_indicator.setStatus(Color.GREEN, autogain_on)
            elif autogain_on is False:
                self.wfs_autogain_indicator.setStatus(Color.BLACK, autogain_on)
            else:
                self.wfs_autogain_indicator.setStatus(Color.RED, autogain_on)

        wfs_emgain = self.consume_stream_keyword(data, config.Streams.NUVU_RAW,
                                                 'EMGAIN')
        if wfs_emgain is not None:
            self.wfs_emgain_lineedit.updateText(emgain=wfs_emgain)

        wfs_exposuretime = self.consume_stream_keyword(data,
                                                       config.Streams.NUVU_RAW,
                                                       'EXPTIME')
        if wfs_exposuretime is not None:
            self.wfs_exposuretime_lineedit.updateText(
                exposuretime=wfs_exposuretime)

        wfs_framerate = self.consume_stream_keyword(data,
                                                    config.Streams.NUVU_RAW,
                                                    'MFRATE')
        if wfs_framerate is not None:
            self.wfs_framerate_lineedit.updateText(framerate=wfs_framerate)

        wfs_temp_ccd = self.consume_stream_keyword(data,
                                                   config.Streams.NUVU_RAW,
                                                   'T_CCD')
        if wfs_temp_ccd is not None:
            self.wfs_ccd_temperature_lineedit.updateText(
                ccd_temperature=wfs_temp_ccd)
