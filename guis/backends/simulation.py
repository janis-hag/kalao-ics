import random
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from astropy.io import fits

from PySide6.QtCore import QTimer

from kalao import database
from kalao.interfaces import fake_data
from kalao.utils import kmath, kstring, zernike
from kalao.utils.rprint import rprint

from guis.backends.abstract import AbstractBackend, emit, timeit
from guis.utils import lorem

from kalao.definitions.dataclasses import LogEntry
from kalao.definitions.enums import (FlipMirrorPosition, IPPowerStatus,
                                     LaserState, LogLevel, PLCStatus,
                                     RelayState, ServiceAction, ShutterState,
                                     TungstenState)

import config


class FakeSHMFPSBackend(AbstractBackend):
    def __init__(self):
        super().__init__()

        self.internal_state = {}

    def _update_stream(self, data, stream_name, stream_data, key=None):
        if key is None:
            key = stream_name

        if key not in data:
            data[key] = {}

        cnt0 = self.internal_state.get(f'{stream_name}-cnt0', -1) + 1

        data[key].update({
            'cnt0': cnt0,
            'data': stream_data,
        })

        self.internal_state[f'{stream_name}-cnt0'] = cnt0

    def _update_stream_keywords(self, data, stream_name, keywords):
        if stream_name not in data:
            data[stream_name] = {}

        data[stream_name]['keywords'] = keywords

    def _update_param(self, data, fps_name, param_name, param):
        if fps_name not in data:
            data[fps_name] = {}

        data[fps_name][param_name] = param

    def _update_dict(self, data, key, dict):
        if key not in data:
            data[key] = {}

        data[key].update(dict)

    def _update_db(self, data, collection, db_data):
        if collection not in data:
            data[collection] = {}

        data[collection].update(db_data)

    def _update_fits_full(self, data, fits_file, hdul):
        key = fits_file.stem

        data[key] = {'mtime': datetime.now(timezone.utc), 'hdul': hdul}

        if fits_file == config.FITS.last_image_all:
            data[key]['mtime'] = self.internal_state.get('fli-mtime')

    def _update_fits_mtime(self, data, fits_file, mtime):
        key = fits_file.stem

        if key not in data:
            data[key] = {}

        data[key]['mtime'] = mtime


class MainBackend(FakeSHMFPSBackend):
    last_camera_update = 0
    first = True

    def __init__(self):
        super().__init__()

        for i in range(12):
            self.internal_state[f'dm01disp{i:02d}'] = zernike.generate_pattern(
                [0], (12, 12))

        for i in range(12):
            self.internal_state[f'dm02disp{i:02d}'] = np.zeros((2, ))

        self.internal_state[config.Streams.MODALGAINS] = np.ones((90, ))
        self.internal_state[config.Streams.MODALGAINS][1:90] = np.linspace(
            1, 0, 89)

        self.internal_state.update({
            'dm-loopON':
                True,
            'dm-loopgain':
                0.9,
            'ttm-loopON':
                True,
            'ttm-loopgain':
                0,
            'nuvu-acq':
                True,
            'nuvu-maqtime':
                0,
            'nuvu-emgain':
                config.WFS.autogain_params[10][0],
            'nuvu-exptime':
                config.WFS.autogain_params[10][1],
            'nuvu-autogain_on':
                True,
            'nuvu-autogain_setting':
                10,
            'bmc-max_stroke':
                0.9,
            'bmc-stroke_mode':
                1,
            'bmc-target_stroke':
                0.2,
            'wfs-algorithm':
                1,
            'shutter_state':
                ShutterState.OPEN,
            'flipmirror_position':
                FlipMirrorPosition.DOWN,
            'calibunit_position':
                config.PLC.initial_state[config.PLC.Node.CALIB_UNIT],
            'calibunit_state':
                PLCStatus.STANDING,
            'laser_state':
                LaserState.OFF,
            'laser_power':
                0,
            'tungsten_state':
                TungstenState.OFF,
            'adc1_angle':
                config.PLC.initial_state[config.PLC.Node.ADC1],
            'adc1_state':
                PLCStatus.STANDING,
            'adc2_angle':
                config.PLC.initial_state[config.PLC.Node.ADC2],
            'adc2_state':
                PLCStatus.STANDING,
            'filterwheel_filter_position':
                4,
            'filterwheel_filter_name':
                'SDSS-z',
            'pump_status':
                RelayState.ON,
            'heater_status':
                RelayState.OFF,
            'fan_status':
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
            'kalao_database-timer.service': ('active', 'running',
                                             datetime.now(timezone.utc)),
            'kalao_hardware-timer.service': ('active', 'running',
                                             datetime.now(timezone.utc)),
            'kalao_observation-timer.service': ('active', 'running',
                                                datetime.now(timezone.utc)),
            'focusing-step':
                0,
        })

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

    def _get_dm01disp(self):
        dm01disp = zernike.generate_pattern([0], (12, 12))
        for i in range(12):
            dm01disp += self.internal_state[f'dm01disp{i:02d}']
        return dm01disp

    def _get_dm02disp(self):
        dm02disp = np.zeros((2, ))
        for i in range(12):
            dm02disp += self.internal_state[f'dm02disp{i:02d}']
        return dm02disp

    def _internal_update(self):
        if time.monotonic() - self.last_camera_update > 5:
            self.internal_state['fli-mtime'] = datetime.now(timezone.utc)
            self.last_camera_update = time.monotonic()

        if self.internal_state['dm-loopON']:
            self.internal_state[
                config.Streams.DM_TURBULENCES] = fake_data.dmdisp()
            self.internal_state[config.Streams.DM_LOOP] = -self.internal_state[
                'dm-loopgain'] * self.internal_state[
                    config.Streams.DM_TURBULENCES]

        if self.internal_state['ttm-loopON']:
            self.internal_state[
                config.Streams.TTM_CENTERING] = fake_data.tiptilt(
                    seed=self.internal_state[config.Streams.TTM_CENTERING])
            self.internal_state[
                config.Streams.TTM_LOOP] = -self.internal_state[
                    'ttm-loopgain'] * self.internal_state[
                        config.Streams.TTM_CENTERING]

    @emit('streams_all_updated')
    @timeit
    def streams_all(self):
        data = {}

        if self.internal_state['flipmirror_position'] == FlipMirrorPosition.UP:
            illumination = 'laser'
            if self.internal_state['laser_state'] == LaserState.OFF:
                flux = 0
            else:
                flux = self.internal_state['laser_power'] / 8 * 2**16
        else:
            illumination = 'telescope'
            if self.internal_state['shutter_state'] == ShutterState.OPEN:
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

        self._update_stream(data, config.Streams.DM, self._get_dm01disp())
        self._update_param(data, config.FPS.BMC, 'max_stroke',
                           self.internal_state['bmc-max_stroke'])

        self._update_stream(
            data, config.Streams.MODE_COEFFS,
            np.random.normal(0, 1, 90) * np.linspace(1, 0, 90)**2)

        if self.internal_state['nuvu-acq']:
            self._update_stream(data, config.Streams.NUVU, wfs_data)

            self._update_stream(data, config.Streams.SLOPES, slopes_data)
            self._update_param(data, config.FPS.SHWFS, 'slope_x_avg',
                               slopes_params['slope_x_avg'])
            self._update_param(data, config.FPS.SHWFS, 'slope_y_avg',
                               slopes_params['slope_y_avg'])
            self._update_param(data, config.FPS.SHWFS, 'residual_rms',
                               slopes_params['residual_rms'])

            self._update_stream(data, config.Streams.FLUX, flux_data)
            self._update_param(data, config.FPS.SHWFS, 'flux_avg',
                               flux_params['flux_avg'])
            self._update_param(data, config.FPS.SHWFS, 'flux_max',
                               flux_params['flux_max'])

        return data

    @emit('camera_image_updated')
    @timeit
    def camera_image(self):
        data = {}

        if self.internal_state['flipmirror_position'] == FlipMirrorPosition.UP:
            illumination = 'laser'
            if self.internal_state['laser_state'] == LaserState.OFF:
                flux = 0
            else:
                flux = self.internal_state['laser_power'] / 8 * 2**16
        else:
            illumination = 'telescope'
            if self.internal_state['shutter_state'] == ShutterState.OPEN:
                flux = 10000
            else:
                flux = 0

        camera_data = fake_data.camera_frame(flux=flux,
                                             dmdisp=self._get_dm01disp(),
                                             tiptilt=self._get_dm02disp(),
                                             illumination=illumination)

        hw = 128
        hdu = fits.PrimaryHDU(camera_data[config.Camera.center_y -
                                          hw:config.Camera.center_y + hw,
                                          config.Camera.center_x -
                                          hw:config.Camera.center_x + hw])
        hdu.header.set(
            'DATE',
            datetime.now(timezone.utc).replace(tzinfo=None).isoformat(
                timespec="milliseconds"))
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

    @emit('all_updated')
    @timeit
    def all(self):
        data = {}

        self._update_fits_mtime(data, config.FITS.last_image_all,
                                self.internal_state['fli-mtime'])

        self._update_stream(data, config.Streams.TTM, self._get_dm02disp())

        if self.first:
            self._update_stream(data, config.Streams.MODALGAINS,
                                self.internal_state[config.Streams.MODALGAINS])
            self.first = False

        if not self.internal_state['nuvu-acq']:
            mfrate = 0
        elif self.internal_state['nuvu-exptime'] < config.WFS.readouttime:
            mfrate = 1000 / config.WFS.readouttime
            self.internal_state['nuvu-maqtime'] = datetime.now(
                timezone.utc).timestamp() * 1e6
        else:
            mfrate = 1000 / self.internal_state['nuvu-exptime']
            self.internal_state['nuvu-maqtime'] = datetime.now(
                timezone.utc).timestamp() * 1e6

        self._update_stream_keywords(
            data, config.Streams.NUVU_RAW, {
                'T_CCD': -60,
                'T_CNTRLR': 35,
                'T_PSU': 35,
                'T_FPGA': 35,
                'T_HSINK': 15.5,
                'EMGAIN': self.internal_state['nuvu-emgain'],
                'DETGAIN': 1,
                'EXPTIME': self.internal_state['nuvu-exptime'],
                'MFRATE': mfrate,
                '_MAQTIME': self.internal_state['nuvu-maqtime'],
            })

        self._update_param(data, config.FPS.NUVU, 'autogain_on',
                           self.internal_state['nuvu-autogain_on'])
        self._update_param(data, config.FPS.NUVU, 'autogain_setting',
                           self.internal_state['nuvu-autogain_setting'])

        self._update_param(data, config.FPS.BMC, 'max_stroke',
                           self.internal_state['bmc-max_stroke'])
        self._update_param(data, config.FPS.BMC, 'stroke_mode',
                           self.internal_state['bmc-stroke_mode'])
        self._update_param(data, config.FPS.BMC, 'target_stroke',
                           self.internal_state['bmc-target_stroke'])

        self._update_param(data, config.FPS.SHWFS, 'algorithm',
                           self.internal_state['wfs-algorithm'])

        self._update_param(data, config.FPS.DMLOOP, 'loopON',
                           self.internal_state['dm-loopON'])
        self._update_param(data, config.FPS.DMLOOP, 'loopgain',
                           self.internal_state['dm-loopgain'])
        self._update_param(data, config.FPS.DMLOOP, 'loopmult', 0.99)
        self._update_param(data, config.FPS.DMLOOP, 'looplimit', 1)

        self._update_param(data, config.FPS.TTMLOOP, 'loopON',
                           self.internal_state['ttm-loopON'])
        self._update_param(data, config.FPS.TTMLOOP, 'loopgain',
                           self.internal_state['ttm-loopgain'])
        self._update_param(data, config.FPS.TTMLOOP, 'loopmult', 0.99)
        self._update_param(data, config.FPS.TTMLOOP, 'looplimit', 1)

        self._update_param(data, config.FPS.CONFIG, 'adc_update', True)
        self._update_param(data, config.FPS.CONFIG, 'ttm_offload', True)

        self._update_dict(
            data, 'plc', {
                'shutter_state':
                    self.internal_state['shutter_state'],
                'flipmirror_position':
                    self.internal_state['flipmirror_position'],
                'calibunit_position':
                    self.internal_state['calibunit_position'],
                'calibunit_state':
                    self.internal_state['calibunit_state'],
                'laser_state':
                    self.internal_state['laser_state'],
                'laser_power':
                    self.internal_state['laser_power'],
                'tungsten_state':
                    self.internal_state['tungsten_state'],
                'adc1_angle':
                    self.internal_state['adc1_angle'],
                'adc1_state':
                    self.internal_state['adc1_state'],
                'adc2_angle':
                    self.internal_state['adc2_angle'],
                'adc2_state':
                    self.internal_state['adc2_state'],
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
                'fan_status':
                    self.internal_state['fan_status'],
                'coolant_flow_rate':
                    2.5
            })

        self._update_dict(
            data, 'services', {
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
                'kalao_database-timer.service':
                    self.internal_state['kalao_database-timer.service'],
                'kalao_hardware-timer.service':
                    self.internal_state['kalao_hardware-timer.service'],
                'kalao_observation-timer.service':
                    self.internal_state['kalao_observation-timer.service'],
            })

        self._update_dict(
            data, 'camera', {
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

        self._update_db(
            data, 'obs', {
                'sequencer_status': [{
                    'value': 'BUSY',
                    'timestamp': datetime(2023, 12, 7, 10, 52, 17)
                }],
                'centering_manual': [{
                    'value': False,
                    'timestamp': datetime(2023, 12, 7, 10, 52, 17)
                }]
            })

        fs = 1.8e3
        noise_power = 0.001 * fs / 2
        timestamps = datetime.now(
            timezone.utc).timestamp() + np.arange(10 * fs) / fs
        tip = 2 * np.sqrt(2) * np.sin(2 * np.pi * 10 * timestamps)
        tip += np.random.normal(scale=np.sqrt(noise_power),
                                size=timestamps.shape)
        tilt = np.sqrt(2) * np.sin(2 * np.pi * 20 * timestamps)
        tilt += np.random.normal(scale=np.sqrt(noise_power),
                                 size=timestamps.shape)

        self._update_stream(
            data, config.Streams.TELEMETRY_TTM,
            np.roll(np.vstack([timestamps, tip, tilt]), 9, axis=1))

        return data

    @emit('monitoringandtelemetry_updated')
    @timeit
    def monitoringandtelemetry(self):
        data = {}

        monitoring_dt = datetime.now(timezone.utc)
        monitoring_dt -= timedelta(
            seconds=monitoring_dt.second %
            config.Database.monitoring_update_interval,
            microseconds=monitoring_dt.microsecond)

        telemetry_dt = datetime.now(timezone.utc)
        telemetry_dt -= timedelta(
            seconds=telemetry_dt.second %
            config.Database.telemetry_update_interval,
            microseconds=telemetry_dt.microsecond)

        self._update_dict(data, 'db-timestamps', {
            'monitoring': monitoring_dt,
            'telemetry': telemetry_dt,
        })

        return data

    @emit('streams_channels_dm_updated')
    @timeit
    def streams_channels_dm(self):
        data = {}

        self._update_stream(data, config.Streams.DM, self._get_dm01disp())

        for i in range(0, 12):
            self._update_stream(
                data, f'{config.Streams.DM}{i:02d}',
                self.internal_state[f'{config.Streams.DM}{i:02d}'])

        return data

    @emit('streams_channels_ttm_updated')
    @timeit
    def streams_channels_ttm(self):
        data = {}

        self._update_stream(data, config.Streams.TTM, self._get_dm02disp())

        for i in range(0, 12):
            self._update_stream(
                data, f'{config.Streams.TTM}{i:02d}',
                self.internal_state[f'{config.Streams.TTM}{i:02d}'])

        return data

    @emit('focus_sequence_updated')
    @timeit
    def focus_sequence(self):
        data = {}

        if self.internal_state['focusing-step'] == config.Focusing.steps:
            return data

        self.internal_state['focusing-step'] %= config.Focusing.steps
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
            i - config.Focusing.steps / 2) * config.Focusing.step_size
        x_star = config.Focusing.window_size / 2
        y_star = config.Focusing.window_size / 2
        peak = 100
        fwhm = 10 + (i - 3.5)**2 + np.random.normal(0, 0.5)

        img_cut = kmath.gaussian_2d_rotated(X, Y, x_star, y_star,
                                            fwhm / kmath.SIGMA_TO_FWHM, fwhm /
                                            kmath.SIGMA_TO_FWHM, 0, peak)

        hdu = fits.ImageHDU(img_cut, name=f'FOCUS{i + 1}')
        hdu.header.set('HIERARCH KAL FOC M2 POS', focus)
        hdu.header.set('HIERARCH KAL FOC STAR X', x_star)
        hdu.header.set('HIERARCH KAL FOC STAR Y', y_star)
        hdu.header.set('HIERARCH KAL FOC STAR PEAK', peak)
        hdu.header.set('HIERARCH KAL FOC STAR FWHM', fwhm)
        hdul.append(hdu)

        if i >= 2:
            xs = []
            ys = []

            for j in range(1, len(hdul)):
                xs.append(hdul[j].header['HIERARCH KAL FOC M2 POS'])
                ys.append(hdul[j].header['HIERARCH KAL FOC STAR FWHM'])

            fit = np.polynomial.polynomial.Polynomial.fit(xs, ys, 2)
            c, b, a = fit.convert().coef

            best_focus = -b / (2*a)
            best_fwhm = fit(best_focus)

            hdul[0].header.set('HIERARCH KAL FOC FIT QUAD', a)
            hdul[0].header.set('HIERARCH KAL FOC FIT LIN', b)
            hdul[0].header.set('HIERARCH KAL FOC FIT CONST', c)

        if i == config.Focusing.steps - 1:
            hdul[0].header.set('HIERARCH KAL FOC BEST M2 POS', best_focus)
            hdul[0].header.set('HIERARCH KAL FOC BEST STAR FWHM', best_fwhm)
            hdul[0].header.set('HIERARCH KAL FOC SUCCESS', True)

        self._update_fits_full(data, config.FITS.last_focus_sequence, hdul)

        return data

    def plots_data(self, *, since, until, monitoring_keys, telemetry_keys,
                   obs_keys):
        now = datetime.now(timezone.utc)
        if until > now:
            until = now

        return {
            'monitoring':
                self._generate_plots_data(
                    monitoring_keys,
                    pd.date_range(
                        since, until,
                        freq=f'{config.Database.monitoring_update_interval}s')
                ),
            'telemetry':
                self._generate_plots_data(
                    telemetry_keys,
                    pd.date_range(
                        since, until,
                        freq=f'{config.Database.telemetry_update_interval}s')),
            'obs':
                self._generate_plots_data(
                    obs_keys, pd.date_range(since, until, freq='300s')),
        }

    def _generate_plots_data(self, keys, timestamps):
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

    def calibration_data(self, *, conf, loop):
        if loop == 1:
            return {
                'wfsref': {
                    'data': np.zeros((11, 22))
                },
                'wfsrefc': {
                    'data': np.zeros((11, 22))
                },
                'wfsmask': {
                    'data': np.zeros((11, 22))
                },
                'wfsmap': {
                    'data': np.zeros((11, 22))
                },
                'CMmodesWFS': {
                    'data': np.zeros((5, 11, 22))
                },
                'dmmask': {
                    'data': np.zeros((12, 12))
                },
                'dmmap': {
                    'data': np.zeros((12, 12))
                },
                'CMmodesDM': {
                    'data': np.zeros((5, 12, 12))
                },
                f'aol{loop}_wfsref': {
                    'data': np.zeros((11, 22))
                },
                f'aol{loop}_wfsrefc': {
                    'data': np.zeros((11, 22))
                },
                f'aol{loop}_wfsmask': {
                    'data': np.zeros((11, 22))
                },
                f'aol{loop}_wfsmap': {
                    'data': np.zeros((11, 22))
                },
                f'aol{loop}_modesWFS': {
                    'data': np.zeros((11, 22, 5))
                },
                f'aol{loop}_dmmask': {
                    'data': np.zeros((12, 12))
                },
                f'aol{loop}_dmmap': {
                    'data': np.zeros((12, 12))
                },
                f'aol{loop}_DMmodes': {
                    'data': np.zeros((12, 12, 5))
                },
            }
        else:
            return {
                'wfsref': {
                    'data': np.zeros((12, 12))
                },
                'wfsrefc': {
                    'data': np.zeros((12, 12))
                },
                'wfsmask': {
                    'data': np.zeros((12, 12))
                },
                'wfsmap': {
                    'data': np.zeros((12, 12))
                },
                'CMmodesWFS': {
                    'data': np.zeros((5, 12, 12))
                },
                'dmmask': {
                    'data': np.zeros((1, 2))
                },
                'dmmap': {
                    'data': np.zeros((1, 2))
                },
                'CMmodesDM': {
                    'data': np.zeros((5, 1, 2))
                },
                f'aol{loop}_wfsref': {
                    'data': np.zeros((12, 12))
                },
                f'aol{loop}_wfsrefc': {
                    'data': np.zeros((12, 12))
                },
                f'aol{loop}_wfsmask': {
                    'data': np.zeros((12, 12))
                },
                f'aol{loop}_wfsmap': {
                    'data': np.zeros((12, 12))
                },
                f'aol{loop}_modesWFS': {
                    'data': np.zeros((12, 12, 5))
                },
                f'aol{loop}_dmmask': {
                    'data': np.zeros((1, 2))
                },
                f'aol{loop}_dmmap': {
                    'data': np.zeros((1, 2))
                },
                f'aol{loop}_DMmodes': {
                    'data': np.zeros((1, 2, 5))
                },
            }

    def calibration_reload(self, *, conf, loop):
        return {'returncode': 0, 'stdout': ''}

    def latency_measure(self, *, conf, loop):
        return {'returncode': 0, 'stdout': ''}

    def RMCM_prepare(self, *, conf, loop):
        return {'returncode': 0, 'stdout': ''}

    def RMCM_mkDMpokemodes(self, *, conf, loop):
        return {'returncode': 0, 'stdout': ''}

    def RMCM_takeref(self, *, conf, loop):
        return {'returncode': 0, 'stdout': ''}

    def RMCM_acqlinResp(self, *, conf, loop):
        return {'returncode': 0, 'stdout': ''}

    def RMCM_RMHdecode(self, *, conf, loop):
        return {'returncode': 0, 'stdout': ''}

    def RMCM_RMmkmask(self, *, conf, loop):
        return {'returncode': 0, 'stdout': ''}

    def RMCM_compCM(self, *, conf, loop):
        return {'returncode': 0, 'stdout': ''}

    def RMCM_load(self, *, conf, loop):
        return {'returncode': 0, 'stdout': ''}

    def RMCM_save(self, *, conf, loop, comment):
        return {'returncode': 0, 'stdout': ''}

    ##### FLI Zoom

    def centering_manual(self, *, dx, dy):
        rprint(f'Centering manually ({dx}, {dy}) (virtually)')

    def centering_validate(self):
        rprint(f'Validated manual centering (virtually)')

    ##### Loop controls

    # DM Loop

    def loops_dm_on(self, *, state):
        self.internal_state['dm-loopON'] = state
        rprint(f'Set DM loop to {state} (virtually)')

    def loops_dm_gain(self, *, gain):
        self.internal_state['dm-loopgain'] = gain
        rprint(f'Set DM gain to {gain} (virtually)')

    def loops_dm_mult(self, *, mult):
        rprint(f'Set DM mult to {mult} (virtually)')

    def loops_dm_limit(self, *, limit):
        rprint(f'Set DM limit to {limit} (virtually)')

    def loops_dm_zero(self):
        rprint(f'DM loop zeroed (virtually)')

    # TTM Loop

    def loops_ttm_on(self, *, state):
        self.internal_state['ttm-loopON'] = state
        rprint(f'Set TTM loop to {state} (virtually)')

    def loops_ttm_gain(self, *, gain):
        self.internal_state['ttm-loopgain'] = gain
        rprint(f'Set TTM gain to {gain} (virtually)')

    def loops_ttm_mult(self, *, mult):
        rprint(f'Set TTM mult to {mult} (virtually)')

    def loops_ttm_limit(self, *, limit):
        rprint(f'Set TTM limit to {limit} (virtually)')

    def loops_ttm_zero(self):
        rprint(f'TTM loop zeroed (virtually)')

    # Wavefront Sensor

    def wfs_emgain(self, *, emgain):
        self.internal_state['nuvu-emgain'] = emgain
        rprint(f'Set Nüvü EM Gain to {emgain} (virtually)')

    def wfs_exposuretime(self, *, exposuretime):
        self.internal_state['nuvu-exptime'] = exposuretime
        rprint(f'Set Nüvü Exposure Time to {exposuretime} (virtually)')

    def wfs_autogain_on(self, *, state):
        self.internal_state['nuvu-autogain_on'] = state

        if state:
            setting = self.internal_state['nuvu-autogain_setting']
            self.internal_state['nuvu-emgain'] = config.WFS.autogain_params[
                setting][0]
            self.internal_state['nuvu-exptime'] = config.WFS.autogain_params[
                setting][1]

        rprint(f'Set Nüvü Auto-gain to {state} (virtually)')

    def wfs_autogain_setting(self, *, setting):
        self.internal_state['nuvu-autogain_setting'] = setting

        if self.internal_state['nuvu-autogain_on']:
            self.internal_state['nuvu-emgain'] = config.WFS.autogain_params[
                setting][0]
            self.internal_state['nuvu-exptime'] = config.WFS.autogain_params[
                setting][1]

        rprint(f'Set Nüvü Auto-gain setting to {setting} (virtually)')

    # Deformable Mirror

    def dm_maxstroke(self, *, stroke):
        self.internal_state['bmc-max_stroke'] = stroke
        rprint(f'Set BMC Max Stroke to {stroke} (virtually)')

    def dm_strokemode(self, *, mode):
        self.internal_state['bmc-stroke_mode'] = mode
        rprint(f'Set BMC Stroke Mode to {mode} (virtually)')

    def dm_targetstroke(self, *, target):
        self.internal_state['bmc-target_stroke'] = target
        rprint(f'Set BMC Target Stroke to {target} (virtually)')

    # Observation

    def adc_update(self, *, state):
        rprint(f'Set ADC Update to {state} (virtually)')

    def ttm_offload(self, *, state):
        rprint(f'Set TTM Offload to {state} (virtually)')

    # Modal gains

    def loops_dm_modalgains(self, *, modalgains):
        self.internal_state[config.Streams.MODALGAINS] = modalgains
        rprint(f'Set Modal Gains to {modalgains} (virtually)')

    ##### Engineering

    def plc_shutter_state(self, *, state):
        self.internal_state['shutter_state'] = ShutterState(state)
        rprint(f'Set Shutter state to {state} (virtually)')

    def plc_shutter_init(self):
        rprint(f'Init Shutter (virtually)')

    def plc_flipmirror_position(self, *, position):
        self.internal_state['flipmirror_position'] = FlipMirrorPosition(
            position)
        rprint(f'Set Flip Mirror position to {position} (virtually)')

    def plc_flipmirror_init(self):
        rprint(f'Init Flip Mirror (virtually)')

    def plc_calibunit_position(self, *, position):
        self._fake_motor_move(position, 'calibunit_position',
                              'calibunit_state', config.CalibUnit.velocity)
        rprint(f'Set Calibration Unit position to {position} (virtually)')

    def plc_calibunit_init(self):
        self._fake_motor_move(0, 'calibunit_position', 'calibunit_state',
                              config.CalibUnit.velocity)
        self._fake_motor_move(
            config.PLC.initial_state[config.PLC.Node.CALIB_UNIT],
            'calibunit_position', 'calibunit_state', config.CalibUnit.velocity)
        rprint(f'Init Calibration Unit (virtually)')

    def plc_calibunit_stop(self):
        rprint(f'Stopped Calibration Unit (virtually)')

    def plc_calibunit_laser(self):
        self._fake_motor_move(config.Laser.position, 'calibunit_position',
                              'calibunit_state', config.CalibUnit.velocity)
        rprint(f'Moved Calibration Unit to Laser position (virtually)')

    def plc_calibunit_tungsten(self):
        self._fake_motor_move(config.Tungsten.position, 'calibunit_position',
                              'calibunit_state', config.CalibUnit.velocity)
        rprint(f'Moved Calibration Unit to Tungsten position (virtually)')

    def plc_tungsten_state(self, *, state):
        if state:
            self.internal_state['tungsten_state'] = TungstenState.ON
        else:
            self.internal_state['tungsten_state'] = TungstenState.OFF

        rprint(f'Set Tungsten state to {state} (virtually)')

    def plc_tungsten_init(self):
        rprint(f'Init Tungsten (virtually)')

    def plc_laser_state(self, *, state):
        if state:
            self.internal_state['laser_state'] = LaserState.ON
        else:
            self.internal_state['laser_state'] = LaserState.OFF

        rprint(f'Set Laser state to {state} (virtually)')

    def plc_laser_power(self, *, power):
        self.internal_state['laser_power'] = power
        rprint(f'Set Laser power to {power} (virtually)')

    def plc_laser_init(self):
        rprint(f'Init Laser (virtually)')

    def plc_lamps_off(self):
        self.internal_state['tungsten_state'] = TungstenState.OFF
        self.internal_state['laser_state'] = LaserState.OFF
        rprint(f'Lamps off (virtually)')

    def plc_filterwheel_filter(self, *, filter):
        self.internal_state[
            'filterwheel_filter_position'] = config.FilterWheel.position_list.index(
                filter)
        self.internal_state['filterwheel_filter_name'] = filter
        rprint(f'Set Filter Wheel filter to {filter} (virtually)')

    def plc_filterwheel_init(self):
        rprint(f'Init Filter Wheel (virtually)')

    def plc_adc1_angle(self, *, position):
        self._fake_motor_move(position, 'adc1_angle', 'adc1_state',
                              config.ADC.velocity)
        rprint(f'Set ADC1 position to {position} (virtually)')

    def plc_adc1_init(self):
        self._fake_motor_move(0, 'adc1_angle', 'adc1_state',
                              config.ADC.velocity)
        self._fake_motor_move(config.PLC.initial_state[config.PLC.Node.ADC1],
                              'adc1_angle', 'adc1_state', config.ADC.velocity)
        rprint(f'Init ADC1 (virtually)')

    def plc_adc1_stop(self):
        rprint(f'Stopped ADC1 (virtually)')

    def plc_adc2_angle(self, *, position):
        self._fake_motor_move(position, 'adc2_angle', 'adc2_state',
                              config.ADC.velocity)
        rprint(f'Set ADC2 position to {position} (virtually)')

    def plc_adc2_init(self):
        self._fake_motor_move(0, 'adc2_angle', 'adc2_state',
                              config.ADC.velocity)
        self._fake_motor_move(config.PLC.initial_state[config.PLC.Node.ADC2],
                              'adc2_angle', 'adc2_state', config.ADC.velocity)
        rprint(f'Init ADC2 (virtually)')

    def plc_adc2_stop(self):
        rprint(f'Stopped ADC2 (virtually)')

    def plc_adc_zerodisp(self):
        # TODO
        rprint(f'Set ADC to zero dispersion (virtually)')

    def plc_adc_maxdisp(self):
        # TODO
        rprint(f'Set ADC to maximum dispersion (virtually)')

    def plc_adc_angleoffset(self, *, angle, offset):
        # TODO
        rprint(f'Set ADC to angle {angle}° and offset {offset}° (virtually)')

    def plc_pump_state(self, *, state):
        if state:
            self.internal_state['pump_status'] = RelayState.ON
        else:
            self.internal_state['pump_status'] = RelayState.OFF

        rprint(f'Set Pump to {state} (virtually)')

    def plc_fan_state(self, *, state):
        if state:
            self.internal_state['fan_status'] = RelayState.ON
        else:
            self.internal_state['fan_status'] = RelayState.OFF

        rprint(f'Set Fan to {state} (virtually)')

    def plc_heater_state(self, *, state):
        if state:
            self.internal_state['heater_status'] = RelayState.ON
        else:
            self.internal_state['heater_status'] = RelayState.OFF

        rprint(f'Set Heater to {state} (virtually)')

    def _fake_motor_move(self, position, position_key, state_key, velocity):
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

    def camera_take(self, *, exposure_time, frames, roi_size):
        rprint(
            f'Started FLI with {frames} exposure(s) of size {roi_size}x{roi_size} and of exposure time {exposure_time} s (virtually)'
        )

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

    def camera_cancel(self):
        self.internal_state['fli-remaining_time'] = 0
        rprint(f'Canceled FLI exposure (virtually)')

    def wfs_acquisition_start(self):
        self.internal_state['nuvu-acq'] = True
        rprint(f'Started Nüvü acquisition (virtually)')

    def wfs_acquisition_stop(self):
        self.internal_state['nuvu-acq'] = False
        rprint(f'Stopped Nüvü acquisition (virtually)')

    def ippower_rtc_on(self):
        self.internal_state['ippower_rtc_status'] = IPPowerStatus.ON
        rprint(f'Powering on RTC (virtually)')

    def ippower_rtc_off(self):
        self.internal_state['ippower_rtc_status'] = IPPowerStatus.OFF
        rprint(f'Powering off RTC (virtually)')

    def ippower_bench_on(self):
        self.internal_state['ippower_bench_status'] = IPPowerStatus.ON
        rprint(f'Powering on Bench (virtually)')

    def ippower_bench_off(self):
        self.internal_state['ippower_bench_status'] = IPPowerStatus.OFF
        rprint(f'Powering off Bench (virtually)')

    def ippower_dm_on(self):
        self.internal_state['ippower_dm_status'] = IPPowerStatus.ON
        rprint(f'Powering on DM (virtually)')

    def ippower_dm_off(self):
        self.internal_state['ippower_dm_status'] = IPPowerStatus.OFF
        rprint(f'Powering off DM (virtually)')

    def centering_laser(self):
        rprint(f'Laser centering launched (virtually)')

    def services_action(self, *, unit, action):
        if action in [ServiceAction.STOP, ServiceAction.KILL]:
            state = ('inactive', '', datetime.now(timezone.utc))
        else:
            state = ('active', '', datetime.now(timezone.utc))

        self.internal_state[unit] = state
        rprint(f'Sent {action} to {unit} (virtually)')

    ##### DM channels

    def channels_resetall(self, *, dm_number):
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

    def channels_reset(self, *, dm_number, channel):
        if dm_number == config.AO.DM_loop_number:
            self.internal_state[
                f'dm01disp{channel:02d}'] = zernike.generate_pattern([0],
                                                                     (12, 12))
        elif dm_number == config.AO.TTM_loop_number:
            self.internal_state[f'dm02disp{channel:02d}'] = np.zeros((2, ))
        else:
            raise Exception(f'Unknown DM number {dm_number}')

        rprint(f'Resetted channel {channel} of DM {dm_number} (virtually)')

    ##### DM & TTM control

    def dm_pattern(self, *, pattern):
        self.internal_state[config.Streams.DM_USER_CONTROLLED] = pattern
        rprint(f'Set DM to {pattern} (virtually)')

    def ttm_position(self, *, array):
        self.internal_state[config.Streams.TTM_USER_CONTROLLED] = array
        rprint(f'Set TTM to {array} (virtually)')

    ##### Focusing

    def focus_autofocus(self):
        rprint('Autofocus launched (virtually)')

    ##### Logs

    def logs_init(self):
        logs = []

        for _ in range(config.GUI.logs_initial_entries):
            logs.append(self._generate_log())

        return logs

    def logs_new(self):
        logs = []

        for _ in range(10):
            logs.append(self._generate_log())

        return logs

    def logs_between(self, *, since, until):
        logs = []

        timestamps = pd.date_range(since, until, freq=f'60s')

        for timestamp in timestamps:
            logs.append(self._generate_log(timestamp))

        return logs

    def _generate_log(self, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now().strftime('%y-%m-%d %H:%M:%S')
        else:
            timestamp = timestamp.strftime('%y-%m-%d %H:%M:%S')

        origin = random.choice(self.logs_services)

        message = lorem.get_random_lorem(8)

        level = random.random()
        if level <= 0.001:
            level = LogLevel.ERROR
            message = '[ERROR] ' + message
        elif level <= 0.011:
            level = LogLevel.WARNING
            message = '[WARNING] ' + message
        else:
            level = LogLevel.INFO
            message = '[INFO] ' + message

        log = random.choice(self.logs_logs)
        if log != '':
            message = f'{log} | {message}'

        return LogEntry(level, timestamp, origin, message)

    ##### Instrument

    def shutdown(self):
        def shutdown(self, *, iknowwhatimdoing):
            if iknowwhatimdoing == 'yes':
                rprint('Shutdown sequence launched')
            else:
                rprint('Shutdown sequence refused')
