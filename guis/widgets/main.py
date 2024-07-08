from datetime import datetime, timezone

import numpy as np

from PySide6.QtCore import QEvent, QObject, Signal
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

from kalao.definitions.enums import CameraStatus

import config


class MainWidget(KWidget, BackendDataMixin):
    hovered = Signal(str)

    activeToolTip = None

    def __init__(self, backend, on_sky_unit=False, parent=None):
        super().__init__(parent)

        self.backend = backend

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
        self.camera = CameraWidget(backend, parent=self)
        self.slopes = SlopesWidget(backend, parent=self)
        self.flux = FluxWidget(backend, parent=self)
        self.dm = DMWidget(backend, parent=self)
        self.ttm = TTMWidget(backend, parent=self)

        self.wfs_frame.layout().addWidget(self.wfs)
        self.camera_frame.layout().addWidget(self.camera)
        self.dm_frame.layout().addWidget(self.dm)
        self.slopes_frame.layout().addWidget(self.slopes)
        self.flux_frame.layout().addWidget(self.flux)
        self.ttm_frame.layout().addWidget(self.ttm)

        for indicator in [
                self.dmloop_indicator, self.ttmloop_indicator,
                self.cameras_status_indicator, self.wfs_acquisition_indicator,
                self.wfs_autogain_indicator
        ]:
            indicator.setCursor(Qt.WhatsThisCursor)
            indicator.installEventFilter(self)

        for widget in [self.camera, self.slopes, self.dm, self.ttm]:
            self.onsky_checkbox.stateChanged.connect(widget.change_units)
            widget.change_units(self.onsky_checkbox.checkState())

        for widget in [self.wfs, self.camera, self.slopes, self.flux, self.dm]:
            self.colormap_checkbox.stateChanged.connect(widget.change_colormap)
            widget.change_colormap(self.colormap_checkbox.checkState())

        for widget in [self.slopes, self.flux, self.dm]:
            self.masks_checkbox.stateChanged.connect(widget.change_mask)
            widget.change_mask(self.masks_checkbox.checkState())

        self.onsky_checkbox.setChecked(on_sky_unit)

        backend.all_updated.connect(self.all_updated)

    def all_updated(self, data):
        ### Instrument

        sequencer_status_v, sequencer_status_t = self.consume_db(
            data, 'obs', 'sequencer_status')
        if sequencer_status_v is not None:
            self.sequencer_lineedit.setText(sequencer_status_v)

        ### AO

        loopON = self.consume_fps_param(data, config.FPS.DMLOOP, 'loopON')
        if loopON is not None:
            if loopON is True:
                self.dmloop_indicator.setStatus(Color.GREEN, loopON)
            elif loopON is False:
                self.dmloop_indicator.setStatus(Color.BLACK, loopON)
            else:
                self.dmloop_indicator.setStatus(Color.RED, loopON)

        loopON = self.consume_fps_param(data, config.FPS.TTMLOOP, 'loopON')
        if loopON is not None:
            if loopON is True:
                self.ttmloop_indicator.setStatus(Color.GREEN, loopON)
            elif loopON is False:
                self.ttmloop_indicator.setStatus(Color.BLACK, loopON)
            else:
                self.ttmloop_indicator.setStatus(Color.RED, loopON)

        ### Camera

        camera_status = self.consume_dict(data, 'camera', 'camera_status')
        if camera_status is not None:
            if camera_status in [
                    CameraStatus.EXPOSING, CameraStatus.READING_CCD
            ]:
                self.cameras_status_indicator.setStatus(
                    Color.GREEN, camera_status)
            elif camera_status in [
                    CameraStatus.IDLE, CameraStatus.WAITING_TRIGGER
            ]:
                self.cameras_status_indicator.setStatus(
                    Color.BLACK, camera_status)
            else:
                self.cameras_status_indicator.setStatus(
                    Color.RED, camera_status)

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

        ccd = self.consume_dict(data, 'camera', 'ccd')
        if ccd is not None:
            self.camera_ccd_temperature_lineedit.updateText(
                ccd_temperature=ccd)

        ### WFS

        maqtime = self.consume_shm_keyword(data, config.SHM.NUVU_RAW,
                                           '_MAQTIME', force=True)
        timestamp = self.consume_metadata(data, 'timestamp')
        if maqtime is not None:
            maqtime = datetime.fromtimestamp(maqtime / 1e6, tz=timezone.utc)
            time_since_last_frame = (timestamp - maqtime).total_seconds()
            if time_since_last_frame < config.WFS.acquisition_time_timeout:
                self.wfs_acquisition_indicator.setStatus(
                    Color.GREEN, time_since_last_frame)
            else:
                self.wfs_acquisition_indicator.setStatus(
                    Color.BLACK, time_since_last_frame)

        autogain_on = self.consume_fps_param(data, config.FPS.NUVU,
                                             'autogain_on')
        if autogain_on is not None:
            if autogain_on is True:
                self.wfs_autogain_indicator.setStatus(Color.GREEN, autogain_on)
            elif autogain_on is False:
                self.wfs_autogain_indicator.setStatus(Color.BLACK, autogain_on)
            else:
                self.wfs_autogain_indicator.setStatus(Color.RED, autogain_on)

        wfs_emgain = self.consume_shm_keyword(data, config.SHM.NUVU_RAW,
                                              'EMGAIN')
        if wfs_emgain is not None:
            self.wfs_emgain_lineedit.updateText(emgain=wfs_emgain)

        wfs_exposuretime = self.consume_shm_keyword(data, config.SHM.NUVU_RAW,
                                                    'EXPTIME')
        if wfs_exposuretime is not None:
            self.wfs_exposuretime_lineedit.updateText(
                exposuretime=wfs_exposuretime)

        wfs_framerate = self.consume_shm_keyword(data, config.SHM.NUVU_RAW,
                                                 'MFRATE')
        if wfs_framerate is not None:
            self.wfs_framerate_lineedit.updateText(framerate=wfs_framerate)

        wfs_ccd_temp = self.consume_shm_keyword(data, config.SHM.NUVU_RAW,
                                                'T_CCD')
        if wfs_ccd_temp is not None:
            self.wfs_ccd_temperature_lineedit.updateText(
                ccd_temperature=wfs_ccd_temp)

    def eventFilter(self, source, event):
        if event.type() == QEvent.ToolTip:
            # Disable tooltips
            return True

        if event.type(
        ) == QEvent.ToolTipChange and source == self.activeToolTip:
            self.hovered.emit(source.toolTip())
        if event.type() == QEvent.Enter:
            self.activeToolTip = source
            self.hovered.emit(source.toolTip())
        elif event.type() == QEvent.Leave:
            self.hovered.emit('')

        return QObject.eventFilter(self, source, event)
