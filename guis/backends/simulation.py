import random
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from PySide6.QtCore import QTimer

from kalao.interfaces import fake_data
from kalao.utils import zernike

from guis.backends.abstract import AbstractBackend, emit, timeit

from kalao.definitions.enums import (FlipMirrorPosition, IPPowerStatus,
                                     LaserState, LogLevel, PLCStatus,
                                     RelayState, ShutterState, TungstenState)

import config


class FakeSHMFPSBackend(AbstractBackend):
    streams_and_fps_cache = {}

    def _update_stream(self, data, stream_name, stream_data, key=None):
        if key is None:
            key = stream_name

        if key not in data:
            data[key] = {}

        cnt0 = data[key].get('cnt0', -1)

        data[key].update({
            'cnt0': cnt0 + 1,
            'data': stream_data,
        })

        if stream_name == 'fli_stream':
            data[key]['cnt0'] = self.data.get('fli_stream', {}).get('cnt0', -1)

    def _update_stream_keywords(self, data, stream_name, keywords):
        if stream_name not in data:
            data[stream_name] = {}

        data[stream_name]['keywords'] = keywords

    def _update_stream_cnt(self, data, stream_name):
        if stream_name not in data:
            data[stream_name] = {}

        cnt0 = data[stream_name].get('cnt0', -1)

        data[stream_name]['cnt0'] = cnt0 + 1

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


class MainBackend(FakeSHMFPSBackend):
    last_fli_update = 0
    first = True

    def __init__(self):
        super().__init__()

        self.internal_state = {}

        for i in range(12):
            self.internal_state[f'dm01disp{i:02d}'] = zernike.generate_pattern(
                [0], (12, 12))

        for i in range(12):
            self.internal_state[f'dm02disp{i:02d}'] = np.zeros((2, ))

        self.internal_state.update({
            'dm-loopON': True,
            'dm-loopgain': 0.9,
            'ttm-loopON': True,
            'ttm-loopgain': 0,
            'shutter_state': ShutterState.OPEN,
            'flip_mirror_position': FlipMirrorPosition.DOWN,
            'calib_unit_position': 24,
            'calib_unit_state': PLCStatus.STANDING,
            'laser_state': LaserState.OFF,
            'laser_power': 0,
            'tungsten_state': TungstenState.OFF,
            'adc1_angle': 45,
            'adc1_state': PLCStatus.STANDING,
            'adc2_angle': -45,
            'adc2_state': PLCStatus.STANDING,
            'filterwheel_filter_position': 4,
            'filterwheel_filter_name': 'z',
            'remaining_time': 0,
            'exposure_time': 60,
            'ippower_rtc_status': IPPowerStatus.ON,
            'ippower_bench_status': IPPowerStatus.ON,
            'ippower_dm_status': IPPowerStatus.OFF,
        })

        self.internal_timer = QTimer()
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
        if time.monotonic() - self.last_fli_update > 0.01:
            self._update_stream_cnt(self.data, config.Streams.FLI)
            self.last_fli_update = time.monotonic()

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

    @emit('streams_updated')
    @timeit
    def get_streams_all(self):
        if self.internal_state['flip_mirror_position'] == FlipMirrorPosition.UP:
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

        nuvu_data = fake_data.nuvu_frame(flux=flux,
                                         dmdisp=self._get_dm01disp(),
                                         tiptilt=self._get_dm02disp(),
                                         illumination=illumination)
        slopes_data = fake_data.slopes(nuvu_data)
        flux_data = fake_data.flux(nuvu_data)

        slopes_params = fake_data.slopes_params(slopes_data)
        flux_params = fake_data.flux_params(flux_data)

        self._update_stream(self.streams, config.Streams.DM,
                            self._get_dm01disp())
        self._update_param(self.streams, config.FPS.BMC, 'max_stroke', 0.9)

        self._update_stream(self.streams, config.Streams.NUVU, nuvu_data)

        self._update_stream(self.streams, config.Streams.SLOPES, slopes_data)
        self._update_param(self.streams, config.FPS.SHWFS, 'slope_x',
                           slopes_params['slope_x'])
        self._update_param(self.streams, config.FPS.SHWFS, 'slope_y',
                           slopes_params['slope_y'])
        self._update_param(self.streams, config.FPS.SHWFS, 'residual',
                           slopes_params['residual'])

        self._update_stream(self.streams, config.Streams.FLUX, flux_data)
        self._update_param(self.streams, config.FPS.SHWFS,
                           'flux_subaperture_avg',
                           flux_params['flux_subaperture_avg'])
        self._update_param(self.streams, config.FPS.SHWFS,
                           'flux_subaperture_brightest',
                           flux_params['flux_subaperture_brightest'])

        return self.streams

    @emit('fli_updated')
    @timeit
    def get_streams_fli(self):
        if self.internal_state['flip_mirror_position'] == FlipMirrorPosition.UP:
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

        fli_data = fake_data.fli_frame(dmdisp=self._get_dm01disp(),
                                       tiptilt=self._get_dm02disp(),
                                       illumination=illumination)

        self._update_stream(self.fli, config.Streams.FLI, fli_data)

        return self.fli

    @emit('data_updated')
    @timeit
    def get_all(self):
        self._update_stream(self.data, config.Streams.TTM,
                            self._get_dm02disp())

        if self.first:
            modalgains = np.ones((90, ))
            modalgains[1:90] = np.linspace(1, 0, 89)

            self._update_stream(self.data, config.Streams.MODALGAINS,
                                modalgains)
            self.first = False

        self._update_stream_keywords(
            self.data, config.Streams.NUVU_RAW, {
                'T_CCD': -60,
                'T_CNTRLR': 35,
                'T_PSU': 35,
                'T_FPGA': 35,
                'T_HSINK': 15.5,
                'EMGAIN': 1000,
                'DETGAIN': 1,
                'EXPTIME': 0.5,
                'MFRATE': 1800,
            })

        self._update_param(self.data, config.FPS.NUVU, 'autogain_on', True)

        self._update_param(self.data, 'mfilt-1', 'loopON',
                           self.internal_state['dm-loopON'])
        self._update_param(self.data, 'mfilt-1', 'loopgain',
                           self.internal_state['dm-loopgain'])
        self._update_param(self.data, 'mfilt-1', 'loopmult', 0.99)
        self._update_param(self.data, 'mfilt-1', 'looplimit', 1)

        self._update_param(self.data, 'mfilt-2', 'loopON',
                           self.internal_state['ttm-loopON'])
        self._update_param(self.data, 'mfilt-2', 'loopgain',
                           self.internal_state['ttm-loopgain'])
        self._update_param(self.data, 'mfilt-2', 'loopmult', 0.99)
        self._update_param(self.data, 'mfilt-2', 'looplimit', 1)

        self._update_dict(
            self.data, 'plc', {
                'shutter_state':
                    self.internal_state['shutter_state'],
                'flip_mirror_position':
                    self.internal_state['flip_mirror_position'],
                'calib_unit_position':
                    self.internal_state['calib_unit_position'],
                'calib_unit_state':
                    self.internal_state['calib_unit_state'],
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
                'temp_bench_air':
                    18.2,
                'temp_bench_board':
                    18.1,
                'temp_water_in':
                    13,
                'temp_water_out':
                    15,
                'pump_status':
                    RelayState.ON,
                'pump_temp':
                    35,
                'heater_status':
                    RelayState.OFF,
                'fan_status':
                    RelayState.ON,
                'flow_value':
                    2.5
            })

        self._update_dict(
            self.data, 'services', {
                'kalao_nuvu.service':
                    ('active', 'exited', datetime(2023, 12, 4, 20, 15, 42)),
                'kalao_cacao.service':
                    ('active', 'exited', datetime(2023, 12, 7, 9, 15, 25)),
                'kalao_sequencer.service':
                    ('active', 'running', datetime(2023, 12, 7, 10, 52, 17)),
                'kalao_camera.service': ('activating', 'auto-restart',
                                         datetime(2023, 12, 7, 10, 52, 17)),
                'kalao_flask-gui.service':
                    ('inactive', 'dead', datetime(1970, 1, 1, 0, 0)),
                'kalao_gop-server.service':
                    ('active', 'running', datetime(2023, 12, 7, 10, 52, 17)),
                'kalao_database-timer.service':
                    ('active', 'running', datetime(2023, 12, 7, 10, 52, 17)),
                'kalao_safety-timer.service':
                    ('active', 'running', datetime(2023, 12, 7, 10, 52, 17)),
                'kalao_loop-timer.service':
                    ('active', 'running', datetime(2023, 12, 7, 10, 52, 17)),
                'kalao_pump-timer.service':
                    ('active', 'running', datetime(2023, 12, 7, 10, 52, 17))
            })

        self._update_dict(
            self.data, 'fli', {
                'remaining_time': self.internal_state['remaining_time'],
                'exposure_time': self.internal_state['exposure_time'],
                'heatsink': 15.5,
                'ccd': -30
            })

        self._update_dict(
            self.data, 'ippower', {
                'ippower_rtc_status':
                    self.internal_state['ippower_rtc_status'],
                'ippower_bench_status':
                    self.internal_state['ippower_bench_status'],
                'ippower_dm_status':
                    self.internal_state['ippower_dm_status'],
            })

        self._update_db(
            self.data, 'obs', {
                'sequencer_status': [{
                    'value': 'BUSY',
                    'timestamp': datetime(2023, 12, 7, 10, 52, 17)
                }],
                'tracking_status': [{
                    'value': 'TRACKING',
                    'timestamp': datetime(2023, 12, 7, 10, 52, 17)
                }]
            })

        return self.data

    @emit('monitoringandtelemetry_updated')
    @timeit
    def get_monitoringandtelemetry(self):
        self.monitoringandtelemetry = {}

        self._update_dict(
            self.monitoringandtelemetry, 'db-timestamps', {
                'monitoring': datetime.now(timezone.utc),
                'telemetry': datetime.now(timezone.utc),
            })

        return self.monitoringandtelemetry

    @emit('dmdisp_updated')
    @timeit
    def get_streams_dmdisp(self, dm_number):
        if dm_number not in self.dmdisp:
            self.dmdisp[dm_number] = {}

        if dm_number == 1:
            self._update_stream(self.dmdisp[dm_number], f'dm01disp',
                                self._get_dm01disp())

            for i in range(0, 12):
                self._update_stream(self.dmdisp[dm_number],
                                    f'dm{dm_number:02d}disp{i:02d}',
                                    self.internal_state[f'dm01disp{i:02d}'])
        else:
            self._update_stream(self.dmdisp[dm_number], f'dm02disp',
                                self._get_dm02disp())

            for i in range(0, 12):
                self._update_stream(self.dmdisp[dm_number],
                                    f'dm{dm_number:02d}disp{i:02d}',
                                    self.internal_state[f'dm02disp{i:02d}'])

        return self.dmdisp[dm_number]

    def plots_data(self, dt_start, dt_end, monitoring_keys, telemetry_keys,
                   obs_keys):
        return {
            'monitoring':
                self._generate_plots_data(
                    monitoring_keys,
                    pd.date_range(
                        dt_start, dt_end,
                        freq=f'{config.Database.monitoring_update_interval}S')
                ),
            'telemetry':
                self._generate_plots_data(
                    telemetry_keys,
                    pd.date_range(
                        dt_start, dt_end,
                        freq=f'{config.Database.telemetry_update_interval}S')),
            'obs':
                self._generate_plots_data(
                    obs_keys, pd.date_range(dt_start, dt_end, freq='300S')),
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

    def get_calibration_data(self, conf, loop):
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

    ##### Loop controls

    # DM Loop

    def set_dm_loop_on(self, state):
        self.internal_state['dm-loopON'] = state
        print(f'Set DM loop to {state} (virtually)')

    def set_dm_loop_gain(self, gain):
        self.internal_state['dm-loopgain'] = gain
        print(f'Set DM gain to {gain} (virtually)')

    def set_dm_loop_mult(self, mult):
        print(f'Set DM mult to {mult} (virtually)')

    def set_dm_loop_limit(self, limit):
        print(f'Set DM limit to {limit} (virtually)')

    # TTM Loop

    def set_ttm_loop_on(self, state):
        self.internal_state['ttm-loopON'] = state
        print(f'Set TTM loop to {state} (virtually)')

    def set_ttm_loop_gain(self, gain):
        self.internal_state['ttm-loopgain'] = gain
        print(f'Set TTM gain to {gain} (virtually)')

    def set_ttm_loop_mult(self, mult):
        print(f'Set TTM mult to {mult} (virtually)')

    def set_ttm_loop_limit(self, limit):
        print(f'Set TTM limit to {limit} (virtually)')

    ##### Engineering

    def set_plc_shutter_state(self, state):
        self.internal_state['shutter_state'] = ShutterState(state)
        print(f'Set Shutter state to {state} (virtually)')

    def set_plc_flipmirror_position(self, position):
        self.internal_state['flip_mirror_position'] = FlipMirrorPosition(
            position)
        print(f'Set Flip Mirror position to {position} (virtually)')

    def set_plc_calibunit_position(self, position):
        self.internal_state['calib_unit_state'] = PLCStatus.MOVING

        if position - self.internal_state['calib_unit_position'] > 0:
            while self.internal_state['calib_unit_position'] < position:
                time.sleep(1)
                self.internal_state[
                    'calib_unit_position'] += config.CalibUnit.velocity

            self.internal_state['calib_unit_state'] = PLCStatus.STANDING
            self.internal_state['calib_unit_position'] = position
        else:
            while self.internal_state['calib_unit_position'] > position:
                time.sleep(1)
                self.internal_state[
                    'calib_unit_position'] -= config.CalibUnit.velocity

            self.internal_state['calib_unit_state'] = PLCStatus.STANDING
            self.internal_state['calib_unit_position'] = position

        print(f'Set Calibration Unit position to {position} (virtually)')

    def set_plc_tungsten_state(self, state):
        if state:
            self.internal_state['tungsten_state'] = TungstenState.ON
        else:
            self.internal_state['tungsten_state'] = TungstenState.OFF
        print(f'Set Tungsten state to {state} (virtually)')

    def set_plc_laser_state(self, state):
        if state:
            self.internal_state['laser_state'] = LaserState.ON
        else:
            self.internal_state['laser_state'] = LaserState.OFF
        print(f'Set Laser state to {state} (virtually)')

    def set_plc_laser_power(self, power):
        self.internal_state['laser_power'] = power
        print(f'Set Laser power to {power} (virtually)')

    def set_plc_filterwheel_filter(self, filter):
        self.internal_state['filterwheel_filter_position'] = 0  #TODO
        self.internal_state['filterwheel_filter_name'] = filter
        print(f'Set Filter Wheel filter to {filter} (virtually)')

    def set_plc_adc_1_angle(self, position):
        self.internal_state['adc1_state'] = PLCStatus.MOVING

        if position - self.internal_state['adc1_angle'] > 0:
            while self.internal_state['adc1_angle'] < position:
                time.sleep(1)
                self.internal_state['adc1_angle'] += config.ADC.velocity

            self.internal_state['adc1_state'] = PLCStatus.STANDING
            self.internal_state['adc1_angle'] = position
        else:
            while self.internal_state['adc1_angle'] > position:
                time.sleep(1)
                self.internal_state['adc1_angle'] -= config.ADC.velocity

            self.internal_state['adc1_state'] = PLCStatus.STANDING
            self.internal_state['adc1_angle'] = position

        print(f'Set ADC1 position to {position} (virtually)')

    def set_plc_adc_2_angle(self, position):
        self.internal_state['adc2_state'] = PLCStatus.MOVING

        if position - self.internal_state['adc2_angle'] > 0:
            while self.internal_state['adc2_angle'] < position:
                time.sleep(1)
                self.internal_state['adc2_angle'] += config.ADC.velocity

            self.internal_state['adc2_state'] = PLCStatus.STANDING
            self.internal_state['adc2_angle'] = position
        else:
            while self.internal_state['adc2_angle'] > position:
                time.sleep(1)
                self.internal_state['adc2_angle'] -= config.ADC.velocity

            self.internal_state['adc2_state'] = PLCStatus.STANDING
            self.internal_state['adc2_angle'] = position

        print(f'Set ADC2 position to {position} (virtually)')

    def set_fli_image(self, exposure_time):
        print(f'Started FLI exposure of {exposure_time} (virtually)')

        self.internal_state['remaining_time'] = exposure_time
        self.internal_state['remaining_time'] = exposure_time

        while self.internal_state['remaining_time'] > 0:
            time.sleep(1)
            if self.internal_state['remaining_time'] > 0:
                self.internal_state['remaining_time'] -= 1

        if self.internal_state['remaining_time'] < 0:
            self.internal_state['remaining_time'] = 0

    def get_fli_cancel(self):
        self.internal_state['remaining_time'] = 0

        print(f'Canceled FLI exposure (virtually)')

    def get_ippower_rtc_on(self):
        self.internal_state['ippower_rtc_status'] = IPPowerStatus.ON
        print(f'Powering on RTC (virtually)')

    def get_ippower_rtc_off(self):
        self.internal_state['ippower_rtc_status'] = IPPowerStatus.OFF
        print(f'Powering off RTC (virtually)')

    def get_ippower_bench_on(self):
        self.internal_state['ippower_bench_status'] = IPPowerStatus.ON
        print(f'Powering on Bench (virtually)')

    def get_ippower_bench_off(self):
        self.internal_state['ippower_bench_status'] = IPPowerStatus.OFF
        print(f'Powering off Bench (virtually)')

    def get_ippower_dm_on(self):
        self.internal_state['ippower_dm_status'] = IPPowerStatus.ON
        print(f'Powering on DM (virtually)')

    def get_ippower_dm_off(self):
        self.internal_state['ippower_dm_status'] = IPPowerStatus.OFF
        print(f'Powering off DM (virtually)')

    def get_centering_star(self):
        print(f'Star centering launched (virtually)')

    def get_centering_laser(self):
        print(f'Laser centering launched (virtually)')

    def set_services_action(self, unit, action):
        print(f'Sent {action} to {unit} (virtually)')

    ##### DM channels

    def reset_dm(self, dm_number):
        if dm_number == 1:
            for i in range(12):
                self.internal_state[
                    f'dm01disp{i:02d}'] = zernike.generate_pattern([0],
                                                                   (12, 12))
        else:
            for i in range(12):
                self.internal_state[f'dm02disp{i:02d}'] = np.zeros((2, ))

        print(f'Resetted DM {dm_number} (virtually)')

    def reset_channel(self, dm_number, channel):
        if dm_number == 1:
            self.internal_state[
                f'dm01disp{channel:02d}'] = zernike.generate_pattern([0],
                                                                     (12, 12))
        else:
            self.internal_state[f'dm02disp{channel:02d}'] = np.zeros((2, ))

        print(f'Resetted channel {channel} of DM {dm_number} (virtually)')

    ##### DM & TTM control

    def set_dm_to(self, array):
        self.internal_state[config.Streams.DM_USER_CONTROLLED] = array
        print(f'Set DM to {array} (virtually)')

    def set_ttm_to(self, array):
        self.internal_state[config.Streams.TTM_USER_CONTROLLED] = array
        print(f'Set TTM to {array} (virtually)')

    ##### Logs

    def get_logs_init(self):
        logs = []

        for _ in range(config.GUI.initial_logs_entries):
            logs.append(self._generate_log())

        return logs

    def get_logs_new(self):
        logs = []

        for _ in range(10):
            logs.append(self._generate_log())

        return logs

    def _generate_log(self):
        timestamp = datetime.now().strftime("%y-%m-%d %H:%M:%S")

        origin = random.sample(sorted(config.Systemd.services), 1)[0]
        origin = config.Systemd.services[origin]['unit'].removeprefix(
            'kalao_').removesuffix('.service')

        message = ' '.join(random.sample(lorem_words, 8))
        message = message[0].upper() + message[1:] + '.'

        level = random.random()

        if level <= 0.001:
            level = LogLevel.ERROR
            message = '[ERROR] ' + message
        elif level <= 0.011:
            level = LogLevel.WARNING
            message = '[WARNING] ' + message
        else:
            level = LogLevel.INFO

        return {
            'level': level,
            'timestamp': timestamp,
            'origin': origin,
            'message': message
        }


lorem = (
    "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim "
    "veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea "
    "commodo consequat. Duis aute irure dolor in reprehenderit in voluptate "
    "velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint "
    "occaecat cupidatat non proident, sunt in culpa qui officia deserunt "
    "mollit anim id est laborum.")

lorem_words = (
    "exercitationem",
    "perferendis",
    "perspiciatis",
    "laborum",
    "eveniet",
    "sunt",
    "iure",
    "nam",
    "nobis",
    "eum",
    "cum",
    "officiis",
    "excepturi",
    "odio",
    "consectetur",
    "quasi",
    "aut",
    "quisquam",
    "vel",
    "eligendi",
    "itaque",
    "non",
    "odit",
    "tempore",
    "quaerat",
    "dignissimos",
    "facilis",
    "neque",
    "nihil",
    "expedita",
    "vitae",
    "vero",
    "ipsum",
    "nisi",
    "animi",
    "cumque",
    "pariatur",
    "velit",
    "modi",
    "natus",
    "iusto",
    "eaque",
    "sequi",
    "illo",
    "sed",
    "ex",
    "et",
    "voluptatibus",
    "tempora",
    "veritatis",
    "ratione",
    "assumenda",
    "incidunt",
    "nostrum",
    "placeat",
    "aliquid",
    "fuga",
    "provident",
    "praesentium",
    "rem",
    "necessitatibus",
    "suscipit",
    "adipisci",
    "quidem",
    "possimus",
    "voluptas",
    "debitis",
    "sint",
    "accusantium",
    "unde",
    "sapiente",
    "voluptate",
    "qui",
    "aspernatur",
    "laudantium",
    "soluta",
    "amet",
    "quo",
    "aliquam",
    "saepe",
    "culpa",
    "libero",
    "ipsa",
    "dicta",
    "reiciendis",
    "nesciunt",
    "doloribus",
    "autem",
    "impedit",
    "minima",
    "maiores",
    "repudiandae",
    "ipsam",
    "obcaecati",
    "ullam",
    "enim",
    "totam",
    "delectus",
    "ducimus",
    "quis",
    "voluptates",
    "dolores",
    "molestiae",
    "harum",
    "dolorem",
    "quia",
    "voluptatem",
    "molestias",
    "magni",
    "distinctio",
    "omnis",
    "illum",
    "dolorum",
    "voluptatum",
    "ea",
    "quas",
    "quam",
    "corporis",
    "quae",
    "blanditiis",
    "atque",
    "deserunt",
    "laboriosam",
    "earum",
    "consequuntur",
    "hic",
    "cupiditate",
    "quibusdam",
    "accusamus",
    "ut",
    "rerum",
    "error",
    "minus",
    "eius",
    "ab",
    "ad",
    "nemo",
    "fugit",
    "officia",
    "at",
    "in",
    "id",
    "quos",
    "reprehenderit",
    "numquam",
    "iste",
    "fugiat",
    "sit",
    "inventore",
    "beatae",
    "repellendus",
    "magnam",
    "recusandae",
    "quod",
    "explicabo",
    "doloremque",
    "aperiam",
    "consequatur",
    "asperiores",
    "commodi",
    "optio",
    "dolor",
    "labore",
    "temporibus",
    "repellat",
    "veniam",
    "architecto",
    "est",
    "esse",
    "mollitia",
    "nulla",
    "a",
    "similique",
    "eos",
    "alias",
    "dolore",
    "tenetur",
    "deleniti",
    "porro",
    "facere",
    "maxime",
    "corrupti",
)

COMMON_WORDS = (
    "lorem",
    "ipsum",
    "dolor",
    "sit",
    "amet",
    "consectetur",
    "adipisicing",
    "elit",
    "sed",
    "do",
    "eiusmod",
    "tempor",
    "incididunt",
    "ut",
    "labore",
    "et",
    "dolore",
    "magna",
    "aliqua",
)
