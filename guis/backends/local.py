from PySide6.QtCore import Signal

from kalao import logs
from kalao.cacao import aocontrol, toolbox
from kalao.plc import (calib_unit, filterwheel, flip_mirror, laser, plc_utils,
                       shutter, tungsten)
from kalao.utils import database

from guis.backends.abstract import AbstractBackend, emit, timeit

from kalao.definitions.enums import LogsOutputType

import config


class SHMFPSBackend(AbstractBackend):
    streams_and_fps_cache = {}

    def _update_stream(self, data, stream_name):
        stream = toolbox.open_stream_once(stream_name,
                                          self.streams_and_fps_cache)

        if stream is None:
            return

        cnt0 = stream.IMAGE.md.cnt0

        if data.get(stream_name, {}).get('cnt0') != cnt0:
            data.update({
                stream_name: {
                    'updated': True,
                    'cnt0': cnt0,
                    'data': stream.get_data(check=False),
                }
            })
        else:
            data.update({stream_name: {'updated': False, 'data': None}})

    def _update_params(self, data, fps_name, param_name):
        fps = toolbox.open_fps_once(fps_name, self.streams_and_fps_cache)

        if fps is None:
            return

        param = fps.get_param(param_name)

        if data.get(fps_name) is None:
            data[fps_name] = {}

        if data.get(fps_name, {}).get(param_name, {}).get('cnt0') != param:
            data[fps_name].update({
                param_name: {
                    'updated': True,
                    'cnt0': param,
                    'value': param
                }
            })
        else:
            data[fps_name].update({
                param_name: {
                    'updated': False,
                    'value': None
                }
            })


class MainBackend(SHMFPSBackend):
    streams_updated = Signal(object)
    streams = {}

    tiptilt_updated = Signal(object)
    tiptilt = {}

    dmdisp_updated = Signal(object)
    dmdisp = {}

    def __init__(self):
        super().__init__()

        self.reader = logs.get_reader(True)

        self.streams['plc'] = {}

    @emit('streams_updated')
    @timeit
    def update_streams(self):
        self._update_stream(self.streams, config.Streams.DM)
        self._update_params(self.streams, config.FPS.BMC, 'max_stroke')

        self._update_stream(self.streams, config.Streams.NUVU)

        self._update_stream(self.streams, config.Streams.SLOPES)
        self._update_params(self.streams, config.FPS.SHWFS, 'slope_x')
        self._update_params(self.streams, config.FPS.SHWFS, 'slope_y')
        self._update_params(self.streams, config.FPS.SHWFS, 'residual')

        self._update_stream(self.streams, config.Streams.FLUX)
        self._update_params(self.streams, config.FPS.SHWFS,
                            'flux_subaperture_avg')
        self._update_params(self.streams, config.FPS.SHWFS,
                            'flux_subaperture_brightest')

        self._update_stream(self.streams, config.Streams.FLI)

        self._update_stream(self.streams, 'aol1_mgainfact')

        self._update_params(self.streams, config.FPS.NUVU, 'autogain_on')

        self._update_params(self.streams, 'mfilt-1', 'loopON')
        self._update_params(self.streams, 'mfilt-1', 'loopgain')
        self._update_params(self.streams, 'mfilt-1', 'loopmult')
        self._update_params(self.streams, 'mfilt-1', 'looplimit')

        self._update_params(self.streams, 'mfilt-2', 'loopON')
        self._update_params(self.streams, 'mfilt-2', 'loopgain')
        self._update_params(self.streams, 'mfilt-2', 'loopmult')
        self._update_params(self.streams, 'mfilt-2', 'looplimit')

        self.streams['plc'].update(plc_utils.get_all_status())

        return self.streams

    @emit('tiptilt_updated')
    @timeit
    def update_tiptilt(self):
        self._update_stream(self.tiptilt, config.Streams.TTM)

        return self.tiptilt

    @emit('dmdisp_updated')
    @timeit
    def update_dmdisp(self, dm_number):
        if dm_number not in self.dmdisp:
            self.dmdisp[dm_number] = {}

        self._update_stream(self.dmdisp[dm_number],
                            f'dm{self.dm_number:02d}disp')

        for i in range(0, 12):
            self._update_stream(self.dmdisp[dm_number],
                                f'dm{self.dm_number:02d}disp{i:02d}')

        return self.dmdisp[dm_number]

    def get_plots_data(self, dt_start, dt_end, monitoring_keys, telemetry_keys,
                       obs_keys):

        data = {}

        if len(monitoring_keys) > 0:
            data['monitoring'] = database.read_mongo_to_pandas_by_timestamp(
                'monitoring', dt_start, dt_end, monitoring_keys)

        if len(telemetry_keys) > 0:
            data['telemetry'] = database.read_mongo_to_pandas_by_timestamp(
                'telemetry', dt_start, dt_end, telemetry_keys)

        if len(obs_keys) > 0:
            data['obs'] = database.read_mongo_to_pandas_by_timestamp(
                'obs', dt_start, dt_end, obs_keys)

        return data

    ##### Loop controls

    # DM Loop

    def set_dm_loop_on(self, state):
        aocontrol.switch_loop(config.AO.DM_loop_number, state)

    def set_dm_loop_gain(selfself, gain):
        aocontrol.set_dmloop_gain(gain)

    def set_dm_loop_mult(selfself, mult):
        aocontrol.set_dmloop_mult(mult)

    def set_dm_loop_limit(selfself, limit):
        aocontrol.set_dmloop_limit(limit)

    # TTM Loop

    def set_ttm_loop_on(self, state):
        aocontrol.switch_loop(config.AO.TTM_loop_number, state)

    def set_ttm_loop_gain(selfself, gain):
        aocontrol.set_ttmloop_gain(gain)

    def set_ttm_loop_mult(selfself, mult):
        aocontrol.set_ttmloop_mult(mult)

    def set_ttm_loop_limit(selfself, limit):
        aocontrol.set_ttmloop_limit(limit)

    ##### Engineering

    def set_shutter_state(self, state):
        shutter._switch(state)

    def set_flipmirror_position(self, position):
        flip_mirror._switch(position)

    def set_calibunit_position(self, position):
        calib_unit.move(position)

    def set_tungsten_state(self, state):
        tungsten.send_command(state)

    def set_laser_state(self, state):
        laser._switch(state)

    def set_laser_intensity(self, intensity):
        laser.set_intensity(intensity)

    def set_filterwheel_filter(self, filter):
        filterwheel.set_filter(filter)

    ##### DM channels

    def reset_dm(self, dm_number):
        aocontrol.reset_dm(dm_number)

    def reset_channel(self, dm_number, channel):
        aocontrol.reset_channel(dm_number, channel)

    ##### Logs

    def init_logs(self):
        entries = []
        for entry in logs.seek(self.reader, LogsOutputType.QT,
                               config.GUI.initial_logs_entries):
            entry['text'] = '<span class="init">' + entry['text'] + '<span>'

            entries.append(entry)

        return entries

    def get_logs(self):
        entries = []

        for entry in logs.get_last_entries(self.reader, LogsOutputType.QT):
            entries.append(entry)

        return entries
