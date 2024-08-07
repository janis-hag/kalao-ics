import random
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd

from astropy.io import fits

from PySide6.QtCore import QTimer

from kalao import database
from kalao.hardware import adc
from kalao.interfaces import fake_data
from kalao.utils import kmath, kstring, ktools, zernike
from kalao.utils.json import KalAOJSONEncoder
from kalao.utils.rprint import rprint

from kalao.guis.backends.abstract import FakeSHMFPSBackend, emit, timeit
from kalao.guis.utils import lorem

from kalao.definitions.dataclasses import CalibrationPose, LogEntry, Template
from kalao.definitions.enums import (CameraServerStatus, CameraStatus,
                                     FlipMirrorStatus, IPPowerStatus,
                                     LaserStatus, LogLevel, PLCStatus,
                                     RelayState, SequencerStatus,
                                     ServiceAction, ShutterStatus, TemplateID,
                                     TungstenStatus, WindowHint)

import config

encoder = KalAOJSONEncoder()


class MainBackend(FakeSHMFPSBackend):
    last_camera_update = 0
    first = True

    def __init__(self) -> None:
        super().__init__()

        for i in range(12):
            self.internal_state[f'dm01disp{i:02d}'] = zernike.generate_pattern(
                [0], (12, 12))

        for i in range(12):
            self.internal_state[f'dm02disp{i:02d}'] = np.zeros((2, ))

        self.internal_state[config.SHM.MODALGAINS] = np.ones((90, ))
        self.internal_state[config.SHM.MODALGAINS][1:90] = np.linspace(
            1, 0, 89)

        self.internal_state.update({
            'dmloop_on':
                True,
            'dmloop_gain':
                0.5,
            'dmloop_mult':
                0.99,
            'dmloop_limit':
                10,
            'ttmloop_on':
                True,
            'ttmloop_gain':
                0.1,
            'ttmloop_mult':
                0.95,
            'ttmloop_limit':
                10,
            'wfs_emgain':
                config.WFS.autogain_params[10][0],
            'wfs_exposuretime':
                config.WFS.autogain_params[10][1],
            'wfs_autogain_on':
                True,
            'wfs_autogain_setting':
                10,
            'wfs_algorithm':
                1,
            'dm_max_stroke':
                0.9,
            'dm_stroke_mode':
                1,
            'dm_target_stroke':
                0.2,
            'ttm_tip':
                0,
            'ttm_tilt':
                0,
            'adc_synchronisation':
                True,
            'ttm_offloading':
                True,
            'shutter_status':
                ShutterStatus.OPEN,
            'flipmirror_status':
                FlipMirrorStatus.DOWN,
            'calibunit_position':
                config.PLC.initial_state[config.PLC.Node.CALIB_UNIT],
            'calibunit_status':
                PLCStatus.STANDING,
            'laser_status':
                LaserStatus.OFF,
            'laser_power':
                0,
            'tungsten_status':
                TungstenStatus.OFF,
            'adc1_angle':
                config.PLC.initial_state[config.PLC.Node.ADC1],
            'adc1_status':
                PLCStatus.STANDING,
            'adc2_angle':
                config.PLC.initial_state[config.PLC.Node.ADC2],
            'adc2_status':
                PLCStatus.STANDING,
            'filterwheel_filter_position':
                4,
            'filterwheel_filter_name':
                'SDSS-z',
            'pump_status':
                RelayState.ON,
            'heater_status':
                RelayState.OFF,
            'heatexchanger_fan_status':
                RelayState.ON,
            'fli-mtime':
                0,
            'fli-exposure_time':
                60,
            'fli-remaining_time':
                0,
            'fli-frames':
                0,
            'fli-remaining_frames':
                0,
            'ippower_rtc_status':
                IPPowerStatus.ON,
            'ippower_bench_status':
                IPPowerStatus.ON,
            'ippower_dm_status':
                IPPowerStatus.ON,
            'kalao_system-setup.service': ('active', 'exited',
                                           datetime.now(timezone.utc)),
            'kalao_tmux-server.service': ('active', 'running',
                                          datetime.now(timezone.utc)),
            'kalao_nuvu.service': ('active', 'exited',
                                   datetime.now(timezone.utc)),
            'kalao_cacao.service': ('active', 'exited',
                                    datetime.now(timezone.utc)),
            'kalao_sequencer.service': ('active', 'running',
                                        datetime.now(timezone.utc)),
            'kalao_fli.service': ('active', 'running',
                                  datetime.now(timezone.utc)),
            'kalao_gop-server.service': ('active', 'running',
                                         datetime.now(timezone.utc)),
            'kalao_monitoring-timer.service': ('active', 'running',
                                               datetime.now(timezone.utc)),
            'kalao_hardware-timer.service': ('active', 'running',
                                             datetime.now(timezone.utc)),
            'kalao_observation-timer.service': ('active', 'running',
                                                datetime.now(timezone.utc)),
            'kalao_mailing-timer.service': ('active', 'running',
                                            datetime.now(timezone.utc)),
            'kalao_gui-backend.service': ('active', 'running',
                                          datetime.now(timezone.utc)),
            'focusing-step':
                0,
            'sequencer_status':
                SequencerStatus.WAITING.value,
            'gui_window_hint':
                ''
        })

        self._update_fli_service()
        self._update_nuvu_service()

        self.logs_logs = ['']
        for key in sorted(database.definitions['logs']['metadata'].keys()):
            self.logs_logs.append(kstring.get_log_name(key))

        self.logs_services = ['systemd']
        for service in config.Systemd.services.values():
            self.logs_services.append(kstring.get_service_name(
                service['unit']))

        self.internal_timer = QTimer(parent=self)
        self.internal_timer.setInterval(100)
        self.internal_timer.timeout.connect(self._internal_update)
        self.internal_timer.start()

    def _get_dm01disp(self) -> np.ndarray:
        dm01disp = zernike.generate_pattern([0], (12, 12))
        for i in range(12):
            dm01disp += self.internal_state[f'dm01disp{i:02d}']
        return dm01disp

    def _get_dm02disp(self) -> np.ndarray:
        dm02disp = np.zeros((2, ))
        for i in range(12):
            dm02disp += self.internal_state[f'dm02disp{i:02d}']
        return dm02disp

    def _update_wfs(self) -> None:
        if not self.internal_state[
                'wfs_acquisition_running'] or self.internal_state[
                    'kalao_nuvu.service'][0] != 'active':
            self.internal_state['wfs_framerate'] = 0
        elif self.internal_state['wfs_exposuretime'] < config.WFS.readouttime:
            self.internal_state['nuvu-maqtime'] = time.time() * 1e6
            self.internal_state['wfs_framerate'] = 1000 / config.WFS.readouttime
        else:
            self.internal_state['nuvu-maqtime'] = time.time() * 1e6
            self.internal_state['wfs_framerate'] = 1000 / self.internal_state[
                'wfs_exposuretime']

    def _update_fli_service(self) -> None:
        if self.internal_state['kalao_fli.service'][0] == 'active':
            self.internal_state['camera_server_status'] = CameraServerStatus.UP
            self.internal_state['camera_status'] = CameraStatus.IDLE
        else:
            self.internal_state[
                'camera_server_status'] = CameraServerStatus.DOWN
            self.internal_state[
                'camera_status'] = CameraStatus.SERVER_UNREACHABLE

    def _update_nuvu_service(self) -> None:
        if self.internal_state['kalao_nuvu.service'][0] == 'active':
            self.internal_state['wfs_acquisition_running'] = True
        else:
            self.internal_state['wfs_acquisition_running'] = False

    def _internal_update(self) -> None:
        if time.monotonic() - self.last_camera_update > 5:
            self.internal_state['fli-mtime'] = datetime.now(timezone.utc)
            self.last_camera_update = time.monotonic()

        if self.internal_state['dmloop_on']:
            self.internal_state[config.SHM.DM_TURBULENCES] = fake_data.dmdisp()
            self.internal_state[config.SHM.DM_LOOP] = -self.internal_state[
                'dmloop_gain'] * self.internal_state[config.SHM.DM_TURBULENCES]

        if self.internal_state['ttmloop_on']:
            self.internal_state[config.SHM.TTM_CENTERING] = fake_data.tiptilt(
                seed=self.internal_state[config.SHM.TTM_CENTERING])
            self.internal_state[config.SHM.TTM_LOOP] = -self.internal_state[
                'ttmloop_gain'] * self.internal_state[config.SHM.TTM_CENTERING]

    def version(self) -> str:
        return config.version

    @emit
    @timeit
    def streams_all(self) -> dict[str, Any]:
        data = {}

        if self.internal_state['flipmirror_status'] == FlipMirrorStatus.UP:
            illumination = 'laser'
            if self.internal_state['laser_status'] == LaserStatus.OFF:
                flux = 0
            else:
                flux = self.internal_state['laser_power'] / 8 * 2**16
        else:
            illumination = 'telescope'
            if self.internal_state['shutter_status'] == ShutterStatus.OPEN:
                flux = 5000
            else:
                flux = 0

        wfs_data = fake_data.wfs_frame(flux=flux, dmdisp=self._get_dm01disp(),
                                       tiptilt=self._get_dm02disp(),
                                       illumination=illumination)
        slopes_data = fake_data.slopes(wfs_data)
        flux_data = fake_data.flux(wfs_data)

        slopes_params = fake_data.slopes_params(slopes_data)
        flux_params = fake_data.flux_params(flux_data)

        self._update_shm(data, config.SHM.DM, self._get_dm01disp())
        self._update_fps_param(data, config.FPS.BMC, 'max_stroke',
                               self.internal_state['dm_max_stroke'])

        self._update_shm(
            data, config.SHM.MODE_COEFFS,
            np.random.normal(0, 1, 90) * np.linspace(1, 0, 90)**2 *
            self.internal_state[config.SHM.MODALGAINS])

        if self.internal_state['wfs_acquisition_running']:
            self.internal_state['wfs_residual_rms'] = slopes_params[
                'residual_rms']
            self.internal_state['wfs_slope_x_avg'] = slopes_params[
                'slope_x_avg']
            self.internal_state['wfs_slope_y_avg'] = slopes_params[
                'slope_y_avg']
            self.internal_state['wfs_flux_avg'] = flux_params['flux_avg']
            self.internal_state['wfs_flux_max'] = flux_params['flux_max']

            self._update_shm(data, config.SHM.NUVU, wfs_data)

            self._update_shm(data, config.SHM.SLOPES, slopes_data)
            self._update_fps_param(data, config.FPS.SHWFS, 'residual_rms',
                                   slopes_params['residual_rms'])
            self._update_fps_param(data, config.FPS.SHWFS, 'slope_x_avg',
                                   slopes_params['slope_x_avg'])
            self._update_fps_param(data, config.FPS.SHWFS, 'slope_y_avg',
                                   slopes_params['slope_y_avg'])

            self._update_shm(data, config.SHM.FLUX, flux_data)
            self._update_fps_param(data, config.FPS.SHWFS, 'flux_avg',
                                   flux_params['flux_avg'])
            self._update_fps_param(data, config.FPS.SHWFS, 'flux_max',
                                   flux_params['flux_max'])

        return data

    @emit
    @timeit
    def camera_image(self) -> dict[str, Any]:
        data = {}

        if self.internal_state['flipmirror_status'] == FlipMirrorStatus.UP:
            illumination = 'laser'
            if self.internal_state['laser_status'] == LaserStatus.OFF:
                flux = 0
            else:
                flux = self.internal_state['laser_power'] / 8 * 2**16
        else:
            illumination = 'telescope'
            if self.internal_state['shutter_status'] == ShutterStatus.OPEN:
                flux = 10000
            else:
                flux = 0

        frames = []
        for i in range(3):
            frames.append(
                fake_data.camera_frame(flux=flux, dmdisp=self._get_dm01disp(),
                                       tiptilt=self._get_dm02disp(),
                                       illumination=illumination))

        hw = 128
        frames = np.array(frames)[:, config.Camera.center_y -
                                  hw:config.Camera.center_y + hw,
                                  config.Camera.center_x -
                                  hw:config.Camera.center_x + hw]
        hdu = fits.PrimaryHDU(frames)
        hdu.header.set(
            'DATE',
            datetime.now(timezone.utc).replace(tzinfo=None).isoformat(
                timespec='milliseconds'))
        hdu.header.set('HIERARCH ESO DET OUT1 PRSCX', 0)
        hdu.header.set('HIERARCH ESO DET OUT1 PRSCY', 0)
        hdu.header.set('HIERARCH ESO DET WIN1 STRX', config.Camera.center_x -
                       hw + 1)  # Note: FITS indexing starts at 1
        hdu.header.set('HIERARCH ESO DET WIN1 STRY', config.Camera.center_y -
                       hw + 1)  # Note: FITS indexing starts at 1
        hdu.header.set('HIERARCH ESO DET WIN1 NX', 2 * hw)
        hdu.header.set('HIERARCH ESO DET WIN1 NY', 2 * hw)
        hdu.header.set('CRPIX1', hw + 1)  # Note: FITS indexing starts at 1
        hdu.header.set('CRPIX2', hw + 1)  # Note: FITS indexing starts at 1

        hdul = fits.HDUList()
        hdul.append(hdu)

        self._update_fits_full(data, config.FITS.last_image_all, hdul)

        return data

    @emit
    @timeit
    def all(self) -> dict[str, Any]:
        data = {}

        self._update_fits_mtime(data, config.FITS.last_image_all,
                                self.internal_state['fli-mtime'])

        dm02disp = self._get_dm02disp()
        self.internal_state['ttm_tip'] = dm02disp[0]
        self.internal_state['ttm_tilt'] = dm02disp[1]
        self._update_shm(data, config.SHM.TTM, dm02disp)

        if self.first:
            self._update_shm(data, config.SHM.MODALGAINS,
                             self.internal_state[config.SHM.MODALGAINS])
            self.first = False

        self._update_wfs()

        self._update_shm_keywords(
            data, config.SHM.NUVU_RAW, {
                'T_CCD': -60,
                'T_CNTRLR': 35,
                'T_PSU': 35,
                'T_FPGA': 35,
                'T_HSINK': 15.5,
                'EMGAIN': self.internal_state['wfs_emgain'],
                'DETGAIN': 1,
                'DETBIAS': 3000,
                'EXPTIME': self.internal_state['wfs_exposuretime'],
                'MFRATE': self.internal_state['wfs_framerate'],
                '_MAQTIME': self.internal_state['nuvu-maqtime'],
            })

        self._update_fps_param(data, config.FPS.NUVU, 'autogain_on',
                               self.internal_state['wfs_autogain_on'])
        self._update_fps_param(data, config.FPS.NUVU, 'autogain_setting',
                               self.internal_state['wfs_autogain_setting'])

        self._update_fps_param(data, config.FPS.BMC, 'max_stroke',
                               self.internal_state['dm_max_stroke'])
        self._update_fps_param(data, config.FPS.BMC, 'stroke_mode',
                               self.internal_state['dm_stroke_mode'])
        self._update_fps_param(data, config.FPS.BMC, 'target_stroke',
                               self.internal_state['dm_target_stroke'])

        self._update_fps_param(data, config.FPS.SHWFS, 'algorithm',
                               self.internal_state['wfs_algorithm'])

        self._update_fps_param(data, config.FPS.DMLOOP, 'loopON',
                               self.internal_state['dmloop_on'])
        self._update_fps_param(data, config.FPS.DMLOOP, 'loopgain',
                               self.internal_state['dmloop_gain'])
        self._update_fps_param(data, config.FPS.DMLOOP, 'loopmult',
                               self.internal_state['dmloop_mult'])
        self._update_fps_param(data, config.FPS.DMLOOP, 'looplimit',
                               self.internal_state['dmloop_limit'])

        self._update_fps_param(data, config.FPS.TTMLOOP, 'loopON',
                               self.internal_state['ttmloop_on'])
        self._update_fps_param(data, config.FPS.TTMLOOP, 'loopgain',
                               self.internal_state['ttmloop_gain'])
        self._update_fps_param(data, config.FPS.TTMLOOP, 'loopmult',
                               self.internal_state['ttmloop_mult'])
        self._update_fps_param(data, config.FPS.TTMLOOP, 'looplimit',
                               self.internal_state['ttmloop_limit'])

        self._update_dict(
            data, 'memory', {
                'sequencer_status':
                    self.internal_state['sequencer_status'],
                'centering_manual_flag':
                    False,
                'centering_timeout':
                    0,
                'adc_synchronisation':
                    self.internal_state['adc_synchronisation'],
                'ttm_offloading':
                    self.internal_state['ttm_offloading'],
                'gui_window_hint':
                    self.internal_state['gui_window_hint'],
            })

        adc_angle, adc_offset = adc._compute_angle_and_offset(
            self.internal_state['adc1_angle'],
            self.internal_state['adc2_angle'])

        self.internal_state['adc_angle'] = adc_angle
        self.internal_state['adc_offset'] = adc_offset

        self._update_dict(
            data, 'hw', {
                'shutter_status':
                    self.internal_state['shutter_status'],
                'flipmirror_status':
                    self.internal_state['flipmirror_status'],
                'calibunit_position':
                    self.internal_state['calibunit_position'],
                'calibunit_status':
                    self.internal_state['calibunit_status'],
                'laser_status':
                    self.internal_state['laser_status'],
                'laser_power':
                    self.internal_state['laser_power'],
                'tungsten_status':
                    self.internal_state['tungsten_status'],
                'adc1_angle':
                    self.internal_state['adc1_angle'],
                'adc1_status':
                    self.internal_state['adc1_status'],
                'adc2_angle':
                    self.internal_state['adc2_angle'],
                'adc2_status':
                    self.internal_state['adc2_status'],
                'adc_angle':
                    self.internal_state['adc_angle'],
                'adc_offset':
                    self.internal_state['adc_offset'],
                'filterwheel_filter_position':
                    self.internal_state['filterwheel_filter_position'],
                'filterwheel_filter_name':
                    self.internal_state['filterwheel_filter_name'],
                'bench_air_temp':
                    18.2,
                'bench_board_temp':
                    18.1,
                'coolant_temp_in':
                    13,
                'coolant_temp_out':
                    15,
                'pump_status':
                    self.internal_state['pump_status'],
                'pump_temp':
                    35,
                'heater_status':
                    self.internal_state['heater_status'],
                'heatexchanger_fan_status':
                    self.internal_state['heatexchanger_fan_status'],
                'coolant_flowrate':
                    2.5
            })

        self._update_dict(
            data, 'services', {
                'kalao_system-setup.service':
                    self.internal_state['kalao_system-setup.service'],
                'kalao_tmux-server.service':
                    self.internal_state['kalao_tmux-server.service'],
                'kalao_nuvu.service':
                    self.internal_state['kalao_nuvu.service'],
                'kalao_cacao.service':
                    self.internal_state['kalao_cacao.service'],
                'kalao_sequencer.service':
                    self.internal_state['kalao_sequencer.service'],
                'kalao_fli.service':
                    self.internal_state['kalao_fli.service'],
                'kalao_gop-server.service':
                    self.internal_state['kalao_gop-server.service'],
                'kalao_monitoring-timer.service':
                    self.internal_state['kalao_monitoring-timer.service'],
                'kalao_hardware-timer.service':
                    self.internal_state['kalao_hardware-timer.service'],
                'kalao_observation-timer.service':
                    self.internal_state['kalao_observation-timer.service'],
                'kalao_mailing-timer.service':
                    self.internal_state['kalao_mailing-timer.service'],
                'kalao_gui-backend.service':
                    self.internal_state['kalao_gui-backend.service'],
            })

        self._update_dict(
            data, 'camera', {
                'camera_status':
                    self.internal_state['camera_status'],
                'exposure_time':
                    self.internal_state['fli-exposure_time'],
                'remaining_time':
                    self.internal_state['fli-remaining_time'],
                'frames':
                    self.internal_state['fli-frames'],
                'remaining_frames':
                    self.internal_state['fli-remaining_frames'],
                'heatsink':
                    15.5,
                'ccd':
                    -30
            })

        self._update_dict(
            data, 'ippower', {
                'ippower_rtc_status':
                    self.internal_state['ippower_rtc_status'],
                'ippower_bench_status':
                    self.internal_state['ippower_bench_status'],
                'ippower_dm_status':
                    self.internal_state['ippower_dm_status'],
            })

        tmux_sessions = ['kalaocam_ctrl', 'nuvu_fgrab']
        if self.internal_state['kalao_cacao.service'][0] == 'active':
            tmux_sessions += config.AO.processes

        self._update_dict(data, 'tmux', {'tmux_sessions': tmux_sessions})

        self._update_dict(data, 'pgrep', {
            'kalaocam_ctrl': 0,
            'nuvu_fgrab': 0,
        })

        status = 'CR' if self.internal_state['kalao_cacao.service'][
            0] == 'active' else 'M'
        for proc in config.AO.processes:
            if proc is None:
                continue

            self._update_fps_md(data, proc, {'status': status})

        for stream in config.AO.streams:
            if stream is None:
                continue

            self._update_shm_md(data, stream)

        time_span = 2
        fs = 1.8e3
        noise_power = 0.001 * fs / 2
        timestamps = time.time() - time_span + np.arange(time_span * fs) / fs
        tip = 2 * np.sqrt(2) * np.sin(2 * np.pi * 10 * timestamps)
        tip += np.random.normal(scale=np.sqrt(noise_power),
                                size=timestamps.shape)
        tilt = np.sqrt(2) * np.sin(2 * np.pi * 20 * timestamps)
        tilt += np.random.normal(scale=np.sqrt(noise_power),
                                 size=timestamps.shape)

        timestamp_offset = np.float32(time.time())

        self._update_shm(
            data, config.SHM.TELEMETRY_TTM,
            np.roll(
                np.vstack([
                    np.full(timestamps.shape, timestamp_offset),
                    timestamps - timestamp_offset,
                    tip,
                    tilt,
                    np.random.normal(loc=1024, scale=16,
                                     size=timestamps.shape),
                    np.random.normal(loc=1280, scale=16,
                                     size=timestamps.shape),
                    np.random.normal(loc=0, scale=0.01, size=timestamps.shape),
                    np.random.normal(loc=0, scale=0.01, size=timestamps.shape),
                    np.random.normal(loc=0, scale=0.01, size=timestamps.shape),
                ]), 9, axis=1))

        return data

    @emit
    @timeit
    def monitoring(self) -> dict[str, Any]:
        data = {}

        monitoring_dt = datetime.now(timezone.utc)
        monitoring_dt -= timedelta(
            seconds=monitoring_dt.second %
            min(config.Monitoring.update_interval,
                config.Monitoring.ao_update_interval),
            microseconds=monitoring_dt.microsecond)

        self._update_dict(data, 'db-timestamps', {
            'monitoring': monitoring_dt,
        })

        data_monitoring = {}
        for key, metadata in database.definitions['monitoring'][
                'metadata'].items():
            if key in self.internal_state:
                value = self.internal_state[key]
                data_monitoring[key] = {
                    'value': value,
                    'timestamp': monitoring_dt
                }

        self._update_db(data, 'monitoring', data_monitoring)

        return data

    @emit
    @timeit
    def streams_channels_dm(self) -> dict[str, Any]:
        data = {}

        dm01disp = self._get_dm01disp()

        self._update_shm(data, config.SHM.DM, dm01disp)
        self._update_shm(data, config.SHM.COMMANDS_DM,
                         np.clip(dm01disp/3.5 + 0.5, 0, 1))

        for i in range(0, 12):
            self._update_shm(data, f'{config.SHM.DM}{i:02d}',
                             self.internal_state[f'{config.SHM.DM}{i:02d}'])

        return data

    @emit
    @timeit
    def streams_channels_ttm(self) -> dict[str, Any]:
        data = {}

        dm02disp = self._get_dm02disp()

        self._update_shm(data, config.SHM.TTM, dm02disp)
        self._update_shm(data, config.SHM.COMMANDS_TTM,
                         np.clip(dm02disp/5 + 0.5, 0, 1))

        for i in range(0, 12):
            self._update_shm(data, f'{config.SHM.TTM}{i:02d}',
                             self.internal_state[f'{config.SHM.TTM}{i:02d}'])

        return data

    @emit
    @timeit
    def focusing_sequence_fits(self) -> dict[str, Any]:
        data = {}

        if self.internal_state['focusing-step'] == config.Focusing.nexp:
            return data

        self.internal_state['focusing-step'] %= config.Focusing.nexp
        self.internal_state['focusing-step'] += 1

        i = self.internal_state['focusing-step'] - 1

        if i == 0:
            hdul = fits.HDUList()
            hdul.append(fits.PrimaryHDU())

            self.internal_state['focusing-hdul'] = hdul
        else:
            hdul = self.internal_state['focusing-hdul']

        x = np.arange(0, config.Focusing.window_size)
        y = np.arange(0, config.Focusing.window_size)

        X, Y = np.meshgrid(x, y)

        focus = config.Focusing.autofocus_f0 + (
            i - config.Focusing.nexp / 2) * config.Focusing.step_size
        x_star = config.Focusing.window_size / 2
        y_star = config.Focusing.window_size / 2
        peak = 100
        fwhm = 10 + (i - 3.5)**2 + np.random.normal(0, 0.5)

        img_cut = kmath.gaussian_2d_rotated(X, Y, x_star, y_star,
                                            fwhm / kmath.SIGMA_TO_FWHM, fwhm /
                                            kmath.SIGMA_TO_FWHM, 0, peak)

        hdu = fits.ImageHDU(img_cut, name=f'FOCUS{i + 1}')
        hdu.header.set('HIERARCH KAO FOC M2 POS', focus)
        hdu.header.set('HIERARCH KAO FOC STAR X', x_star)
        hdu.header.set('HIERARCH KAO FOC STAR Y', y_star)
        hdu.header.set('HIERARCH KAO FOC STAR PEAK', peak)
        hdu.header.set('HIERARCH KAO FOC STAR FWHM', fwhm)
        hdul.append(hdu)

        if i >= 2:
            xs = []
            ys = []

            for j in range(1, len(hdul)):
                xs.append(hdul[j].header['HIERARCH KAO FOC M2 POS'])
                ys.append(hdul[j].header['HIERARCH KAO FOC STAR FWHM'])

            fit = np.polynomial.polynomial.Polynomial.fit(xs, ys, 2)
            c, b, a = fit.convert().coef

            best_focus = -b / (2*a)
            best_fwhm = fit(best_focus)

            hdul[0].header.set('HIERARCH KAO FOC FIT QUAD', a)
            hdul[0].header.set('HIERARCH KAO FOC FIT LIN', b)
            hdul[0].header.set('HIERARCH KAO FOC FIT CONST', c)

        if i == config.Focusing.nexp - 1:
            hdul[0].header.set('HIERARCH KAO FOC BEST M2 POS', best_focus)
            hdul[0].header.set('HIERARCH KAO FOC BEST STAR FWHM', best_fwhm)
            hdul[0].header.set('HIERARCH KAO FOC SUCCESS', True)

            self.internal_state[
                'sequencer_status'] = SequencerStatus.WAITING.value

        self._update_fits_full(data, config.FITS.last_focus_sequence, hdul)

        return data

    @emit
    @timeit
    def calibration_sequence(self) -> dict[str, Any]:
        data = {}

        calib_list = []

        template = Template(id=TemplateID.BIAS, start=None, nexp=5)
        for expno in range(template.nexp):
            calib_list.append(
                CalibrationPose(template=template, filter=None,
                                exposure_time=0.001))

        for j in range(3):
            template = Template(id=TemplateID.DARK, start=None, nexp=5)
            for i in range(template.nexp):
                calib_list.append(
                    CalibrationPose(template=template, filter=None,
                                    exposure_time=10 * (j+1)))

        for f in config.Calib.Flats.default_flat_list:
            template = Template(id=TemplateID.LAMP_FLAT, start=None, nexp=1)
            calib_list.append(
                CalibrationPose(
                    template=template, filter=f,
                    exposure_time=config.Calib.Flats.tungsten_exptime_list[f]))

        self._update_dict(data, 'memory', {
            'calibration_poses': {
                'list': encoder.encode(calib_list)
            }
        })

        return data

    @emit
    @timeit
    def centering_spiral_data(self) -> dict[str, Any]:
        data = {}

        self._update_dict(
            data, 'memory', {
                'spiral_search': {
                    'radius': 1,
                    'overlap': 0.15,
                    'expno': 7,
                    'star_x': 128,
                    'star_y': -896
                }
            })

        return data

    def sequencer_abort(self) -> None:
        rprint('Aborted sequence (virtually)')

    def plots_data_db(self, *, since: datetime, until: datetime,
                      monitoring_keys: list[str],
                      obs_keys: list[str]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        if until > now:
            until = now

        return {
            'monitoring':
                self._generate_plots_data(
                    monitoring_keys,
                    pd.date_range(
                        since, until,
                        freq=f'{config.Monitoring.update_interval}s')),
            'obs':
                self._generate_plots_data(
                    obs_keys, pd.date_range(since, until, freq='300s')),
        }

    def plots_data_live(self) -> dict[str, Any]:
        data = {}
        data['timestamp'] = datetime.now(timezone.utc)
        for key in database.definitions['monitoring']['metadata'].keys():
            data[key] = np.random.normal(0, 1)

        return data

    def _generate_plots_data(self, keys, timestamps) -> pd.DataFrame:
        data = {}
        for key in keys:
            data[key] = {
                timestamp: value
                for timestamp, value in zip(
                    timestamps,
                    np.cumsum(np.random.normal(0, 1, len(timestamps))))
            }

        df = pd.DataFrame(data, columns=keys)

        return df

    def ao_calibration_data(self, *, conf: str, loop: int) -> dict[str, Any]:
        if loop == 1:
            wfsref = np.zeros((11, 22))
            wfsrefc = wfsref
            wfsmask = ktools.generate_dm_wfsmask()
            wfsmap = ktools.get_wfs_flux_map()
            dmmask = ktools.generate_dm_dmmask()
            dmmap = ktools.get_dm_flux_map()

            for i in config.WFS.masked_subaps:
                if i in config.WFS.masked_subaps:
                    j, k = ktools.get_subaperture_2d(i)
                    wfsmap[j, k] = 0

            wfsmap = np.concatenate([wfsmap, wfsmap], axis=1)

            CMmodesWFS = []
            CMmodesDM = []

            modes = 6

            for i in range(1, modes):
                coeffs = np.zeros(modes)
                coeffs[i] = 1 / i
                dm = zernike.generate_pattern(coeffs, (12, 12))
                CMmodesDM.append(dm * dmmask)
                CMmodesWFS.append(
                    zernike.slopes_from_pattern_interp(dm) * wfsmask)

            CMmodesDM = np.array(CMmodesDM)
            CMmodesWFS = np.array(CMmodesWFS)
        else:
            wfsref = ktools.generate_ttm_wfsrefc()
            wfsrefc = wfsref
            wfsmask = ktools.generate_ttm_wfsmask()
            wfsmap = ktools.get_dm_flux_map()
            dmmask = ktools.generate_ttm_dmmask()
            dmmap = np.array([1, 1])

            wfsmap *= ktools.generate_dm_dmmask()

            CMmodesWFS = []
            CMmodesDM = []

            CMmodesWFS.append(
                zernike.generate_pattern([0, 5, 0], (12, 12)) * wfsmask)
            CMmodesWFS.append(
                zernike.generate_pattern([0, 0, 5], (12, 12)) * wfsmask)

            CMmodesDM.append([
                [1, 0],
            ])
            CMmodesDM.append([
                [0, 1],
            ])

            CMmodesDM = np.array(CMmodesDM)
            CMmodesWFS = np.array(CMmodesWFS)

        return {
            'wfsref': {
                'data': wfsref
            },
            'wfsrefc': {
                'data': wfsrefc
            },
            'wfsmask': {
                'data': wfsmask
            },
            'wfsmap': {
                'data': wfsmap
            },
            'CMmodesWFS': {
                'data': CMmodesWFS
            },
            'dmmask': {
                'data': dmmask
            },
            'dmmap': {
                'data': dmmap
            },
            'CMmodesDM': {
                'data': CMmodesDM
            },
            f'aol{loop}_wfsref': {
                'data': wfsref
            },
            f'aol{loop}_wfsrefc': {
                'data': wfsrefc
            },
            f'aol{loop}_wfsmask': {
                'data': wfsmask
            },
            f'aol{loop}_wfsmap': {
                'data': wfsmap
            },
            f'aol{loop}_modesWFS': {
                'data': np.transpose(CMmodesWFS, (1, 2, 0))
            },
            f'aol{loop}_dmmask': {
                'data': dmmask
            },
            f'aol{loop}_dmmap': {
                'data': dmmap
            },
            f'aol{loop}_DMmodes': {
                'data': np.transpose(CMmodesDM, (1, 2, 0))
            }
        }

    def ao_calibration_reload(self, *, conf: str, loop: int) -> dict[str, Any]:
        return {
            'returncode': 0,
            'stdout': lorem.get_paragraphs(20, 3, 10).replace('\n', '\n\n')
        }

    def ao_calibration_prepare(self, *, conf: str,
                               loop: int) -> dict[str, Any]:
        return {
            'returncode': 0,
            'stdout': lorem.get_paragraphs(20, 3, 10).replace('\n', '\n\n')
        }

    def ao_calibration_mlat(self, *, conf: str, loop: int) -> dict[str, Any]:
        time.sleep(1)

        data = {
            'returncode': 0,
            'stdout': lorem.get_paragraphs(20, 3, 10).replace('\n', '\n\n')
        }

        framerate = 1805.71
        dt = 1 / framerate

        if loop == 1:
            latency = 2.2
            spread = 1
        else:
            latency = 7
            spread = 2

        t = np.linspace(-latency * dt, 5 * latency * dt, 1000)

        y = 1 - np.abs((2/spread) * (t/dt - latency))
        y[y < 0] = 0
        y += np.random.normal(0, 0.05, y.shape)

        data['hardwlatencypts'] = np.transpose(
            np.array([np.zeros(t.shape), t, y]), (1, 0))

        self._update_fps_param(data, f'mlat-{loop}', 'out.latencyfr', latency)
        self._update_fps_param(data, f'mlat-{loop}', 'out.framerateHz',
                               framerate)

        return data

    def ao_calibration_mkDMpokemodes(self, *, conf: str,
                                     loop: int) -> dict[str, Any]:
        time.sleep(1)

        return {
            'returncode': 0,
            'stdout': lorem.get_paragraphs(20, 3, 10).replace('\n', '\n\n')
        }

    def ao_calibration_takeref(self, *, conf: str,
                               loop: int) -> dict[str, Any]:
        time.sleep(1)

        return {
            'returncode': 0,
            'stdout': lorem.get_paragraphs(20, 3, 10).replace('\n', '\n\n')
        }

    def ao_calibration_acqlinResp(self, *, conf: str,
                                  loop: int) -> dict[str, Any]:
        time.sleep(1)

        return {
            'returncode': 0,
            'stdout': lorem.get_paragraphs(20, 3, 10).replace('\n', '\n\n')
        }

    def ao_calibration_RMHdecode(self, *, conf: str,
                                 loop: int) -> dict[str, Any]:
        time.sleep(1)

        data = {
            'returncode': 0,
            'stdout': lorem.get_paragraphs(20, 3, 10).replace('\n', '\n\n')
        }

        array = []

        if loop == 1:
            flux_map = ktools.get_dm_flux_map()

            for i in range(140):
                dm = np.zeros((12, 12))

                j, k = ktools.get_actuator_2d(i)
                dm[j, k] = 0.1 * flux_map[j, k]

                array.append(zernike.slopes_from_pattern_interp(dm))

        else:
            array.append(zernike.generate_pattern([0, 1, 0], (12, 12)))
            array.append(zernike.generate_pattern([0, 0, 1], (12, 12)))

        self._update_fits(data, 'zrespM-H.fits', np.array(array))

        return data

    def ao_calibration_RMmkmask(self, *, conf: str,
                                loop: int) -> dict[str, Any]:
        time.sleep(1)

        return {
            'returncode': 0,
            'stdout': lorem.get_paragraphs(20, 3, 10).replace('\n', '\n\n')
        }

    def ao_calibration_compCM(self, *, conf: str, loop: int) -> dict[str, Any]:
        time.sleep(1)

        return {
            'returncode': 0,
            'stdout': lorem.get_paragraphs(20, 3, 10).replace('\n', '\n\n')
        }

    def ao_calibration_load(self, *, conf: str, loop: int) -> dict[str, Any]:
        return {
            'returncode': 0,
            'stdout': lorem.get_paragraphs(20, 3, 10).replace('\n', '\n\n')
        }

    def ao_calibration_save(self, *, conf: str, loop: int,
                            comment: str) -> dict[str, Any]:
        return {
            'returncode': 0,
            'stdout': lorem.get_paragraphs(20, 3, 10).replace('\n', '\n\n')
        }

    ##### Science Camera

    def centering_manual_offsets(self, *, dx: float, dy: float) -> None:
        rprint(f'Centering manually ({dx}, {dy}) (virtually)')

    def centering_manual_validate(self) -> None:
        rprint('Validated manual centering (virtually)')

    ##### Loop controls

    # DM Loop

    def ao_dmloop_on(self, *, state: bool) -> None:
        self.internal_state['dmloop_on'] = state
        rprint(f'Set DM loop to {state} (virtually)')

    def ao_dmloop_gain(self, *, gain: float) -> None:
        self.internal_state['dmloop_gain'] = gain
        rprint(f'Set DM gain to {gain} (virtually)')

    def ao_dmloop_mult(self, *, mult: float) -> None:
        self.internal_state['dmloop_mult'] = mult
        rprint(f'Set DM mult to {mult} (virtually)')

    def ao_dmloop_limit(self, *, limit: float) -> None:
        self.internal_state['dmloop_limit'] = limit
        rprint(f'Set DM limit to {limit} (virtually)')

    def ao_dmloop_zero(self) -> None:
        rprint('DM loop zeroed (virtually)')

    # TTM Loop

    def ao_ttmloop_on(self, *, state: bool) -> None:
        self.internal_state['ttmloop_on'] = state
        rprint(f'Set TTM loop to {state} (virtually)')

    def ao_ttmloop_gain(self, *, gain: float) -> None:
        self.internal_state['ttmloop_gain'] = gain
        rprint(f'Set TTM gain to {gain} (virtually)')

    def ao_ttmloop_mult(self, *, mult: float) -> None:
        self.internal_state['ttmloop_mult'] = mult
        rprint(f'Set TTM mult to {mult} (virtually)')

    def ao_ttmloop_limit(self, *, limit: float) -> None:
        self.internal_state['ttmloop_limit'] = limit
        rprint(f'Set TTM limit to {limit} (virtually)')

    def ao_ttmloop_zero(self) -> None:
        rprint('TTM loop zeroed (virtually)')

    # Wavefront Sensor

    def wfs_emgain(self, *, emgain: int) -> None:
        self.internal_state['wfs_emgain'] = emgain
        rprint(f'Set Nüvü EM Gain to {emgain} (virtually)')

    def wfs_exposuretime(self, *, exposuretime: float) -> None:
        self.internal_state['wfs_exposuretime'] = exposuretime
        rprint(f'Set Nüvü Exposure Time to {exposuretime} (virtually)')

    def wfs_autogain_on(self, *, state: bool) -> None:
        self.internal_state['wfs_autogain_on'] = state

        if state:
            setting = self.internal_state['wfs_autogain_setting']
            self.internal_state['wfs_emgain'] = config.WFS.autogain_params[
                setting][0]
            self.internal_state[
                'wfs_exposuretime'] = config.WFS.autogain_params[setting][1]

        rprint(f'Set Nüvü Auto-gain to {state} (virtually)')

    def wfs_autogain_setting(self, *, setting: int) -> None:
        self.internal_state['wfs_autogain_setting'] = setting

        if self.internal_state['wfs_autogain_on']:
            self.internal_state['wfs_emgain'] = config.WFS.autogain_params[
                setting][0]
            self.internal_state[
                'wfs_exposuretime'] = config.WFS.autogain_params[setting][1]

        rprint(f'Set Nüvü Auto-gain setting to {setting} (virtually)')

    # Deformable Mirror

    def dm_maxstroke(self, *, stroke: float) -> None:
        self.internal_state['dm_max_stroke'] = stroke
        rprint(f'Set BMC Max Stroke to {stroke} (virtually)')

    def dm_strokemode(self, *, mode: int) -> None:
        self.internal_state['dm_stroke_mode'] = mode
        rprint(f'Set BMC Stroke Mode to {mode} (virtually)')

    def dm_targetstroke(self, *, target: float) -> None:
        self.internal_state['dm_target_stroke'] = target
        rprint(f'Set BMC Target Stroke to {target} (virtually)')

    # Observation

    def adc_synchronisation(self, *, state: bool) -> None:
        self.internal_state['adc_synchronisation'] = state
        rprint(f'Set ADC Synchronization to {state} (virtually)')

    def ttm_offloading(self, *, state: bool) -> None:
        self.internal_state['ttm_offloading'] = state
        rprint(f'Set TTM Offloading to {state} (virtually)')

    # Modal gains

    def ao_dmloop_modalgains(self, *, modalgains: np.ndarray) -> None:
        self.internal_state[config.SHM.MODALGAINS] = modalgains
        rprint(f'Set Modal Gains to {modalgains} (virtually)')

    ##### Engineering

    # PLC / Misc. hardware

    def hardware_shutter_status(self, *, status: str) -> None:
        self.internal_state['shutter_status'] = ShutterStatus(status)
        rprint(f'Set Shutter status to {status} (virtually)')

    def hardware_shutter_init(self) -> None:
        rprint('Init Shutter (virtually)')

    def hardware_flipmirror_status(self, *, status: str) -> None:
        self.internal_state['flipmirror_status'] = FlipMirrorStatus(status)
        rprint(f'Set Flip Mirror status to {status} (virtually)')

    def hardware_flipmirror_init(self) -> None:
        rprint('Init Flip Mirror (virtually)')

    def hardware_calibunit_position(self, *, position: float) -> None:
        self._fake_motor_move(position, 'calibunit_position',
                              'calibunit_status', config.CalibUnit.velocity)
        rprint(f'Set Calibration Unit position to {position} (virtually)')

    def hardware_calibunit_init(self) -> None:
        self._fake_motor_move(0, 'calibunit_position', 'calibunit_status',
                              config.CalibUnit.velocity)
        self._fake_motor_move(
            config.PLC.initial_state[config.PLC.Node.CALIB_UNIT],
            'calibunit_position', 'calibunit_status',
            config.CalibUnit.velocity)
        rprint('Init Calibration Unit (virtually)')

    def hardware_calibunit_stop(self) -> None:
        rprint('Stopped Calibration Unit (virtually)')

    def hardware_calibunit_laser(self) -> None:
        self._fake_motor_move(config.Laser.position, 'calibunit_position',
                              'calibunit_status', config.CalibUnit.velocity)
        rprint('Moved Calibration Unit to Laser position (virtually)')

    def hardware_calibunit_tungsten(self) -> None:
        self._fake_motor_move(config.Tungsten.position, 'calibunit_position',
                              'calibunit_status', config.CalibUnit.velocity)
        rprint('Moved Calibration Unit to Tungsten position (virtually)')

    def hardware_tungsten_status(self, *, status: bool) -> None:
        if status:
            self.internal_state['tungsten_status'] = TungstenStatus.ON
        else:
            self.internal_state['tungsten_status'] = TungstenStatus.OFF

        rprint(f'Set Tungsten status to {status} (virtually)')

    def hardware_tungsten_init(self) -> None:
        rprint('Init Tungsten (virtually)')

    def hardware_laser_status(self, *, status: bool) -> None:
        if status:
            self.internal_state['laser_status'] = LaserStatus.ON
        else:
            self.internal_state['laser_status'] = LaserStatus.OFF

        rprint(f'Set Laser status to {status} (virtually)')

    def hardware_laser_power(self, *, power: float) -> None:
        self.internal_state['laser_power'] = power
        rprint(f'Set Laser power to {power} (virtually)')

    def hardware_laser_init(self) -> None:
        rprint('Init Laser (virtually)')

    def hardware_lamps_off(self) -> None:
        self.internal_state['tungsten_status'] = TungstenStatus.OFF
        self.internal_state['laser_status'] = LaserStatus.OFF
        rprint('Lamps off (virtually)')

    def hardware_filterwheel_filter(self, *, filter: str) -> None:
        self.internal_state[
            'filterwheel_filter_position'] = config.FilterWheel.position_list.index(
                filter)
        self.internal_state['filterwheel_filter_name'] = filter
        rprint(f'Set Filter Wheel filter to {filter} (virtually)')

    def hardware_filterwheel_init(self) -> None:
        rprint('Init Filter Wheel (virtually)')

    def hardware_adc1_angle(self, *, position: float) -> None:
        self._fake_motor_move(position, 'adc1_angle', 'adc1_status',
                              config.ADC.velocity)
        rprint(f'Set ADC1 position to {position} (virtually)')

    def hardware_adc1_init(self) -> None:
        self._fake_motor_move(0, 'adc1_angle', 'adc1_status',
                              config.ADC.velocity)
        self._fake_motor_move(config.PLC.initial_state[config.PLC.Node.ADC1],
                              'adc1_angle', 'adc1_status', config.ADC.velocity)
        rprint('Init ADC1 (virtually)')

    def hardware_adc1_stop(self) -> None:
        rprint('Stopped ADC1 (virtually)')

    def hardware_adc2_angle(self, *, position: float) -> None:
        self._fake_motor_move(position, 'adc2_angle', 'adc2_status',
                              config.ADC.velocity)
        rprint(f'Set ADC2 position to {position} (virtually)')

    def hardware_adc2_init(self) -> None:
        self._fake_motor_move(0, 'adc2_angle', 'adc2_status',
                              config.ADC.velocity)
        self._fake_motor_move(config.PLC.initial_state[config.PLC.Node.ADC2],
                              'adc2_angle', 'adc2_status', config.ADC.velocity)
        rprint('Init ADC2 (virtually)')

    def hardware_adc2_stop(self) -> None:
        rprint('Stopped ADC2 (virtually)')

    def hardware_adc_zerodisp(self) -> None:
        # TODO
        rprint('Set ADC to zero dispersion (virtually)')

    def hardware_adc_maxdisp(self) -> None:
        # TODO
        rprint('Set ADC to maximum dispersion (virtually)')

    def hardware_adc_angleoffset(self, *, angle: float, offset: float) -> None:
        # TODO
        rprint(f'Set ADC to angle {angle}° and offset {offset}° (virtually)')

    def hardware_pump_status(self, *, status: bool) -> None:
        if status:
            self.internal_state['pump_status'] = RelayState.ON
        else:
            self.internal_state['pump_status'] = RelayState.OFF

        rprint(f'Set Pump to {status} (virtually)')

    def hardware_fan_status(self, *, status: bool) -> None:
        if status:
            self.internal_state['heatexchanger_fan_status'] = RelayState.ON
        else:
            self.internal_state['heatexchanger_fan_status'] = RelayState.OFF

        rprint(f'Set Fan to {status} (virtually)')

    def hardware_heater_status(self, *, status: bool) -> None:
        if status:
            self.internal_state['heater_status'] = RelayState.ON
        else:
            self.internal_state['heater_status'] = RelayState.OFF

        rprint(f'Set Heater to {status} (virtually)')

    def _fake_motor_move(self, position, position_key, state_key,
                         velocity) -> None:
        self.internal_state[state_key] = PLCStatus.MOVING

        if position - self.internal_state[position_key] > 0:
            step = velocity
        else:
            step = -velocity

        while np.abs(self.internal_state[position_key] -
                     position) > np.abs(step):
            self.internal_state[position_key] += step
            time.sleep(1)

        self.internal_state[state_key] = PLCStatus.STANDING
        self.internal_state[position_key] = position

    # Camera

    def camera_exptime(self, *, exposure_time: float) -> None:
        self.internal_state['fli-exposure_time'] = exposure_time
        rprint(f'Set exposure time to {exposure_time} s (virtually)')

    def camera_take(self, *, exposure_time: float, frames: int,
                    roi_size: int) -> None:
        rprint(
            f'Started camera with {frames} exposure(s) of size {roi_size}x{roi_size} and of exposure time {exposure_time} s (virtually)'
        )

        self.internal_state['camera_status'] = CameraStatus.EXPOSING
        self.internal_state['fli-frames'] = frames
        self.internal_state['fli-remaining_frames'] = frames

        while self.internal_state['fli-remaining_frames'] > 0:
            self.internal_state['fli-exposure_time'] = exposure_time
            self.internal_state['fli-remaining_time'] = exposure_time

            while self.internal_state['fli-remaining_time'] > 0:
                time.sleep(1)
                if self.internal_state['fli-remaining_time'] > 0:
                    self.internal_state['fli-remaining_time'] -= 1

            if self.internal_state['fli-remaining_time'] < 0:
                self.internal_state['fli-remaining_time'] = 0

            self.internal_state['fli-remaining_frames'] -= 1

        self.internal_state['camera_status'] = CameraStatus.READING_CCD

        time.sleep(1)

        self.internal_state['camera_status'] = CameraStatus.IDLE

    def camera_cancel(self) -> None:
        self.internal_state['fli-remaining_time'] = 0
        rprint('Canceled camera exposure (virtually)')

    # Wavefront Sensor

    def wfs_acquisition_start(self) -> None:
        self.internal_state['wfs_acquisition_running'] = True
        rprint('Started Nüvü acquisition (virtually)')

    def wfs_acquisition_stop(self) -> None:
        self.internal_state['wfs_acquisition_running'] = False
        rprint('Stopped Nüvü acquisition (virtually)')

    # Deformable Mirror

    def dm_on(self) -> None:
        self.internal_state['ippower_dm_status'] = IPPowerStatus.ON
        rprint('Turned on DM (virtually)')

    def dm_off(self) -> None:
        self.internal_state['ippower_dm_status'] = IPPowerStatus.OFF
        rprint('Turned off DM (virtually)')

    # IPPower

    def ippower_rtc_on(self) -> None:
        self.internal_state['ippower_rtc_status'] = IPPowerStatus.ON
        rprint('Powering on RTC (virtually)')

    def ippower_rtc_off(self) -> None:
        self.internal_state['ippower_rtc_status'] = IPPowerStatus.OFF
        rprint('Powering off RTC (virtually)')

    def ippower_bench_on(self) -> None:
        self.internal_state['ippower_bench_status'] = IPPowerStatus.ON
        rprint('Powering on Bench (virtually)')

    def ippower_bench_off(self) -> None:
        self.internal_state['ippower_bench_status'] = IPPowerStatus.OFF
        rprint('Powering off Bench (virtually)')

    def ippower_dm_on(self) -> None:
        self.internal_state['ippower_dm_status'] = IPPowerStatus.ON
        rprint('Powering on DM (virtually)')

    def ippower_dm_off(self) -> None:
        self.internal_state['ippower_dm_status'] = IPPowerStatus.OFF
        rprint('Powering off DM (virtually)')

    # Services

    def services_action(self, *, unit: str, action: str) -> None:
        if action == ServiceAction.START and self.internal_state[unit][
                0] == 'inactive':
            self.internal_state[unit] = ('activating', '',
                                         datetime.now(timezone.utc))
            time.sleep(5)
            self.internal_state[unit] = ('active', '',
                                         datetime.now(timezone.utc))
            if unit == 'kalao_fli.service':
                self._update_fli_service()
            elif unit == 'kalao_nuvu.service':
                self._update_nuvu_service()
        elif action == ServiceAction.STOP and self.internal_state[unit][
                0] == 'active':
            self.internal_state[unit] = ('deactivating', '',
                                         datetime.now(timezone.utc))
            if unit == 'kalao_fli.service':
                self._update_fli_service()
            elif unit == 'kalao_nuvu.service':
                self._update_nuvu_service()
            time.sleep(5)
            self.internal_state[unit] = ('inactive', '',
                                         datetime.now(timezone.utc))
        elif action == ServiceAction.RESTART:
            if self.internal_state[unit][0] == 'active':
                self.internal_state[unit] = ('deactivating', '',
                                             datetime.now(timezone.utc))
                if unit == 'kalao_fli.service':
                    self._update_fli_service()
                elif unit == 'kalao_nuvu.service':
                    self._update_nuvu_service()
                time.sleep(5)
            self.internal_state[unit] = ('activating', '',
                                         datetime.now(timezone.utc))
            time.sleep(5)
            self.internal_state[unit] = ('active', '',
                                         datetime.now(timezone.utc))
            if unit == 'kalao_fli.service':
                self._update_fli_service()
            elif unit == 'kalao_nuvu.service':
                self._update_nuvu_service()
        elif action == ServiceAction.KILL:
            self.internal_state[unit] = ('inactive', '',
                                         datetime.now(timezone.utc))
            if unit == 'kalao_fli.service':
                self._update_fli_service()
            elif unit == 'kalao_nuvu.service':
                self._update_nuvu_service()
        elif action == ServiceAction.RELOAD and self.internal_state[unit][
                0] == 'active':
            self.internal_state[unit] = ('reloading', '',
                                         datetime.now(timezone.utc))
            time.sleep(5)
            self.internal_state[unit] = ('active', '',
                                         datetime.now(timezone.utc))

        rprint(f'Sent {action} to {unit} (virtually)')

    # DM channels

    def channels_resetall(self, *, dm_number: int) -> None:
        if dm_number == config.AO.DM_loop_number:
            for i in range(12):
                self.internal_state[
                    f'dm01disp{i:02d}'] = zernike.generate_pattern([0],
                                                                   (12, 12))
        elif dm_number == config.AO.TTM_loop_number:
            for i in range(12):
                self.internal_state[f'dm02disp{i:02d}'] = np.zeros((2, ))
        else:
            raise Exception(f'Unknown DM number {dm_number}')

        rprint(f'Resetted DM {dm_number} (virtually)')

    def channels_reset(self, *, dm_number: int, channel: int) -> None:
        if dm_number == config.AO.DM_loop_number:
            self.internal_state[
                f'dm01disp{channel:02d}'] = zernike.generate_pattern([0],
                                                                     (12, 12))
        elif dm_number == config.AO.TTM_loop_number:
            self.internal_state[f'dm02disp{channel:02d}'] = np.zeros((2, ))
        else:
            raise Exception(f'Unknown DM number {dm_number}')

        rprint(f'Resetted channel {channel} of DM {dm_number} (virtually)')

    # DM & TTM control

    def dm_pattern(self, *, pattern: np.ndarray) -> None:
        self.internal_state[config.SHM.DM_USER_CONTROLLED] = pattern
        rprint(f'Set DM to {pattern} (virtually)')

    def ttm_position(self, *, tip: float, tilt: float) -> None:
        array = np.array([tip, tilt])
        self.internal_state[config.SHM.TTM_USER_CONTROLLED] = array
        rprint(f'Set TTM to {array} (virtually)')

    # Centering

    def centering_star(self) -> None:
        rprint('Star centering launched (virtually)')

    def centering_laser(self) -> None:
        rprint('Laser centering launched (virtually)')

    def centering_spiral(self) -> None:
        self.internal_state['gui_window_hint'] = WindowHint.SPIRAL_SEARCH
        rprint('Spiral search launched (virtually)')

    # Focusing

    def focusing_autofocus(self) -> None:
        rprint('Autofocus launched (virtually)')

    def focusing_sequence(self) -> None:
        self.internal_state['gui_window_hint'] = WindowHint.FOCUS_SEQUENCE
        self.internal_state['focusing-step'] = 0
        self.internal_state['sequencer_status'] = SequencerStatus.FOCUSING.value
        rprint('Focus sequence launched (virtually)')

    # Dead-man

    def deadman(self, *, count: int) -> None:
        rprint('Dead-man triggered (virtually)')

    # Instrument / RTC

    def instrument_shutdown(self) -> None:
        rprint('Shutdown sequence initiated (virtually)')

    def rtc_poweroff(self) -> None:
        rprint('RTC power off initiated (virtually)')

    def rtc_reboot(self) -> None:
        rprint('RTC reboot initiated (virtually)')

    ##### Logs

    def logs(self, *, timestamp: datetime = None, cursor: str = None,
             lines: int = None) -> list[LogEntry]:
        logs = []

        if lines is None:
            lines = 10

        for _ in range(lines):
            logs.append(self._generate_log_entry())

        return logs

    def logs_between(self, *, since: datetime,
                     until: datetime) -> list[LogEntry]:
        logs = []

        timestamps = pd.date_range(since, until, freq='60s')

        for timestamp in timestamps:
            logs.append(self._generate_log_entry(timestamp.to_pydatetime()))

        return logs

    def _generate_log_entry(self, timestamp: datetime = None) -> LogEntry:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        origin = random.choice(self.logs_services)

        message = lorem.get_sentence(8)

        level = random.choices([
            LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO
        ], [1, 10, 1000])[0]
        message = f'[{level.value}] {message}'

        log = random.choice(self.logs_logs)
        if log != '':
            message = f'{log} | {message}'

        return LogEntry(cursor='', level=level, timestamp=timestamp,
                        origin=origin, message=message)
