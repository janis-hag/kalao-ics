from typing import Any

import numpy as np

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget

from compiled.ui_main import Ui_MainWidget

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.widgets import KWidget
from kalao.guis.widgets.camera import CameraWidget
from kalao.guis.widgets.dm import DMWidget
from kalao.guis.widgets.flux import FluxWidget
from kalao.guis.widgets.slopes import SlopesWidget
from kalao.guis.widgets.ttm import TTMWidget
from kalao.guis.widgets.wfs import WFSWidget

from kalao.definitions.enums import CameraStatus

import config


class MainWidget(KWidget, BackendDataMixin):
    hovered = Signal(str)

    activeToolTip = None

    def __init__(self, backend: AbstractBackend, on_sky_unit: bool = False,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend

        self.ui = Ui_MainWidget()
        self.ui.setupUi(self)

        self.resize(1300, 900)

        self.ui.camera_exposure_time_spinbox.setValue(np.nan)
        self.ui.camera_remaining_time_spinbox.setValue(np.nan)
        self.ui.camera_remaining_frames_spinbox.setValue(-1)
        self.ui.camera_ccd_temperature_spinbox.setValue(np.nan)
        self.ui.wfs_emgain_spinbox.setValue(-1)
        self.ui.wfs_exposuretime_spinbox.setValue(np.nan)
        self.ui.wfs_framerate_spinbox.setValue(np.nan)
        self.ui.wfs_ccd_temperature_spinbox.setValue(np.nan)

        self.wfs = WFSWidget(backend, parent=self)
        self.camera = CameraWidget(backend, parent=self)
        self.slopes = SlopesWidget(backend, parent=self)
        self.flux = FluxWidget(backend, parent=self)
        self.dm = DMWidget(backend, parent=self)
        self.ttm = TTMWidget(backend, parent=self)

        self.ui.wfs_frame.layout().addWidget(self.wfs)
        self.ui.camera_frame.layout().addWidget(self.camera)
        self.ui.dm_frame.layout().addWidget(self.dm)
        self.ui.slopes_frame.layout().addWidget(self.slopes)
        self.ui.flux_frame.layout().addWidget(self.flux)
        self.ui.ttm_frame.layout().addWidget(self.ttm)

        for indicator in [
                self.ui.dmloop_indicator, self.ui.ttmloop_indicator,
                self.ui.cameras_status_indicator,
                self.ui.wfs_acquisition_indicator,
                self.ui.wfs_autogain_indicator
        ]:
            indicator.setCursor(Qt.CursorShape.WhatsThisCursor)
            indicator.installEventFilter(self)

        for widget in [self.camera, self.slopes, self.dm, self.ttm]:
            self.ui.onsky_checkbox.stateChanged.connect(widget.change_units)
            widget.change_units(self.ui.onsky_checkbox.checkState())

        for widget in [self.wfs, self.camera, self.slopes, self.flux, self.dm]:
            self.ui.colormap_checkbox.stateChanged.connect(
                widget.change_colormap)
            widget.change_colormap(self.ui.colormap_checkbox.checkState())

        for widget in [self.slopes, self.flux, self.dm]:
            self.ui.masks_checkbox.stateChanged.connect(widget.change_mask)
            widget.change_mask(self.ui.masks_checkbox.checkState())

        self.ui.onsky_checkbox.setChecked(on_sky_unit)

        backend.all_updated.connect(self.all_updated)

    def all_updated(self, data: dict[str, Any]) -> None:
        ### Instrument

        sequencer_status = self.consume_dict(data, 'memory',
                                             'sequencer_status')
        if sequencer_status is not None:
            self.ui.sequencer_lineedit.setText(sequencer_status)

        ### AO

        loopON = self.consume_fps_param(data, config.FPS.DMLOOP, 'loopON')
        if loopON is not None:
            if loopON is True:
                self.ui.dmloop_indicator.setStatus(Color.GREEN, loopON)
            elif loopON is False:
                self.ui.dmloop_indicator.setStatus(Color.BLACK, loopON)
            else:
                self.ui.dmloop_indicator.setStatus(Color.RED, loopON)

        loopON = self.consume_fps_param(data, config.FPS.TTMLOOP, 'loopON')
        if loopON is not None:
            if loopON is True:
                self.ui.ttmloop_indicator.setStatus(Color.GREEN, loopON)
            elif loopON is False:
                self.ui.ttmloop_indicator.setStatus(Color.BLACK, loopON)
            else:
                self.ui.ttmloop_indicator.setStatus(Color.RED, loopON)

        ### Camera

        camera_status = self.consume_dict(data, 'camera', 'camera_status')
        if camera_status is not None:
            if camera_status in [
                    CameraStatus.EXPOSING, CameraStatus.READING_CCD
            ]:
                self.ui.cameras_status_indicator.setStatus(
                    Color.GREEN, camera_status)
            elif camera_status in [
                    CameraStatus.IDLE, CameraStatus.WAITING_TRIGGER
            ]:
                self.ui.cameras_status_indicator.setStatus(
                    Color.BLACK, camera_status)
            else:
                self.ui.cameras_status_indicator.setStatus(
                    Color.RED, camera_status)

        exposure_time = self.consume_dict(data, 'camera', 'exposure_time')
        if exposure_time is not None:
            self.ui.camera_exposure_time_spinbox.setValue(exposure_time)

        remaining_time = self.consume_dict(data, 'camera', 'remaining_time')
        if remaining_time is not None:
            self.ui.camera_remaining_time_spinbox.setValue(remaining_time)

        remaining_frames = self.consume_dict(data, 'camera',
                                             'remaining_frames')
        if remaining_frames is not None:
            self.ui.camera_remaining_frames_spinbox.setValue(remaining_frames)

        ccd = self.consume_dict(data, 'camera', 'ccd')
        if ccd is not None:
            self.ui.camera_ccd_temperature_spinbox.setValue(ccd)

        ### WFS

        maqtime = self.consume_shm_keyword(data, config.SHM.NUVU_RAW,
                                           '_MAQTIME', force=True)
        if maqtime is not None:
            time_since_last_frame = self.consume_metadata(
                data, 'timestamp') - maqtime/1e6
            if time_since_last_frame < config.WFS.acquisition_time_timeout:
                self.ui.wfs_acquisition_indicator.setStatus(
                    Color.GREEN, time_since_last_frame)
            else:
                self.ui.wfs_acquisition_indicator.setStatus(
                    Color.BLACK, time_since_last_frame)

        autogain_on = self.consume_fps_param(data, config.FPS.NUVU,
                                             'autogain_on')
        if autogain_on is not None:
            if autogain_on is True:
                self.ui.wfs_autogain_indicator.setStatus(
                    Color.GREEN, autogain_on)
            elif autogain_on is False:
                self.ui.wfs_autogain_indicator.setStatus(
                    Color.BLACK, autogain_on)
            else:
                self.ui.wfs_autogain_indicator.setStatus(
                    Color.RED, autogain_on)

        wfs_emgain = self.consume_shm_keyword(data, config.SHM.NUVU_RAW,
                                              'EMGAIN')
        if wfs_emgain is not None:
            self.ui.wfs_emgain_spinbox.setValue(wfs_emgain)

        wfs_exposuretime = self.consume_shm_keyword(data, config.SHM.NUVU_RAW,
                                                    'EXPTIME')
        if wfs_exposuretime is not None:
            self.ui.wfs_exposuretime_spinbox.setValue(wfs_exposuretime)

        wfs_framerate = self.consume_shm_keyword(data, config.SHM.NUVU_RAW,
                                                 'MFRATE')
        if wfs_framerate is not None:
            self.ui.wfs_framerate_spinbox.setValue(wfs_framerate)

        wfs_ccd_temp = self.consume_shm_keyword(data, config.SHM.NUVU_RAW,
                                                'T_CCD')
        if wfs_ccd_temp is not None:
            self.ui.wfs_ccd_temperature_spinbox.setValue(wfs_ccd_temp)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.ToolTip:
            # Disable tooltips
            return True

        if event.type(
        ) == QEvent.Type.ToolTipChange and source == self.activeToolTip:
            self.hovered.emit(source.toolTip())
        if event.type() == QEvent.Type.Enter:
            self.activeToolTip = source
            self.hovered.emit(source.toolTip())
        elif event.type() == QEvent.Type.Leave:
            self.activeToolTip = None
            self.hovered.emit('')

        return QObject.eventFilter(self, source, event)
