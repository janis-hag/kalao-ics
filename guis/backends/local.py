from datetime import datetime
from pathlib import Path

from astropy.io import fits

from kalao import ippower, logs, services
from kalao.cacao import aocontrol, toolbox
from kalao.fli import camera
from kalao.plc import (adc, calib_unit, filterwheel, flip_mirror, laser,
                       plc_utils, shutter, tungsten)
from kalao.utils import centering, database

from guis.backends.abstract import AbstractBackend, emit, timeit

from kalao.definitions.enums import IPPowerStatus, LogsOutputType

import config


class SHMFPSBackend(AbstractBackend):
    streams_and_fps_cache = {}

    def _update_stream(self, data, stream_name, key=None):
        if key is None:
            key = stream_name

        stream = toolbox.open_stream_once(stream_name,
                                          self.streams_and_fps_cache)

        if stream is None:
            return

        if key not in data:
            data[key] = {}

        data[key].update({
            'cnt0': stream.IMAGE.md.cnt0,
            'data': stream.get_data(check=False),
        })

    def _update_stream_keywords(self, data, stream_name):
        stream = toolbox.open_stream_once(stream_name,
                                          self.streams_and_fps_cache)

        if stream is None:
            return

        if stream_name not in data:
            data[stream_name] = {}

        data[stream_name]['keywords'] = stream.get_keywords()

    def _update_stream_cnt(self, data, stream_name):
        stream = toolbox.open_stream_once(stream_name,
                                          self.streams_and_fps_cache)

        if stream is None:
            return

        if data.get(stream_name) is None:
            data[stream_name] = {}

        data[stream_name]['cnt0'] = stream.IMAGE.md.cnt0,

    def _update_param(self, data, fps_name, param_name, fps_missing=None):
        if fps_name not in data:
            data[fps_name] = {}

        fps = toolbox.open_fps_once(fps_name, self.streams_and_fps_cache)

        if fps is None:
            if fps_missing is not None:
                data[fps_name][param_name] = fps_missing
        else:
            data[fps_name][param_name] = fps.get_param(param_name)

    def _update_dict(self, data, key, dict):
        if key not in data:
            data[key] = {}

        data[key].update(dict)

    def _update_db(self, data, collection, db_data):
        if collection not in data:
            data[collection] = {}

        data[collection].update(db_data)

    def _update_fits(self, data, fits_file):
        fits_file = Path(fits_file)
        key = fits_file.stem

        data[key] = {
            'mtime': datetime.fromtimestamp(fits_file.stat().st_mtime),
            'data': fits.getdata(fits_file),
        }


class MainBackend(SHMFPSBackend):
    def __init__(self):
        super().__init__()

        self.reader = logs.get_reader(True)

    @emit('streams_updated')
    @timeit
    def get_streams_all(self):
        self._update_stream(self.streams, config.Streams.DM)
        self._update_param(self.streams, config.FPS.BMC, 'max_stroke')

        self._update_stream(self.streams, config.Streams.NUVU)

        self._update_stream(self.streams, config.Streams.SLOPES)
        self._update_param(self.streams, config.FPS.SHWFS, 'slope_x')
        self._update_param(self.streams, config.FPS.SHWFS, 'slope_y')
        self._update_param(self.streams, config.FPS.SHWFS, 'residual')

        self._update_stream(self.streams, config.Streams.FLUX)
        self._update_param(self.streams, config.FPS.SHWFS,
                           'flux_subaperture_avg')
        self._update_param(self.streams, config.FPS.SHWFS,
                           'flux_subaperture_brightest')

        return self.streams

    @emit('fli_updated')
    @timeit
    def get_streams_fli(self):
        self._update_stream(self.fli, config.Streams.FLI)

        return self.fli

    @emit('data_updated')
    @timeit
    def get_all(self):
        self._update_stream_cnt(self.data, config.Streams.FLI)

        self._update_stream(self.data, config.Streams.TTM)
        self._update_stream(self.data, config.Streams.MODALGAINS)

        self._update_stream_keywords(self.data, config.Streams.NUVU_RAW)

        self._update_param(self.data, config.FPS.NUVU, 'autogain_on')

        self._update_param(self.data, 'mfilt-1', 'loopON')
        self._update_param(self.data, 'mfilt-1', 'loopgain')
        self._update_param(self.data, 'mfilt-1', 'loopmult')
        self._update_param(self.data, 'mfilt-1', 'looplimit')

        self._update_param(self.data, 'mfilt-2', 'loopON')
        self._update_param(self.data, 'mfilt-2', 'loopgain')
        self._update_param(self.data, 'mfilt-2', 'loopmult')
        self._update_param(self.data, 'mfilt-2', 'looplimit')

        self._update_dict(self.data, 'plc', plc_utils.get_all_status())
        self._update_dict(self.data, 'services', services.get_all_status())
        self._update_dict(self.data, 'fli', camera.get_exposure_status())
        self._update_dict(self.data, 'fli', camera.get_temperatures())
        self._update_dict(self.data, 'ippower', ippower.status_all())

        self._update_db(
            self.data, 'obs',
            database.get('obs', ['sequencer_status', 'tracking_status']))

        return self.data

    @emit('monitoringandtelemetry_updated')
    @timeit
    def get_monitoringandtelemetry(self):
        self._update_db(self.monitoringandtelemetry, 'monitoring',
                        database.get('monitoring'))
        self._update_db(self.monitoringandtelemetry, 'telemetry',
                        database.get('telemetry'))

        return self.monitoringandtelemetry

    @emit('dmdisp_updated')
    @timeit
    def get_streams_dmdisp(self, dm_number):
        if dm_number not in self.dmdisp:
            self.dmdisp[dm_number] = {}

        self._update_stream(self.dmdisp[dm_number], f'dm{dm_number:02d}disp')

        for i in range(0, 12):
            self._update_stream(self.dmdisp[dm_number],
                                f'dm{dm_number:02d}disp{i:02d}')

        return self.dmdisp[dm_number]

    def plots_data(self, dt_start, dt_end, monitoring_keys, telemetry_keys,
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

    def get_calibration_data(self, conf, loop):
        data = {}

        self._update_fits(
            data,
            config.AO.cacao_workdir / f'setupfiles/{conf}/conf/wfsref.fits')
        self._update_fits(
            data,
            config.AO.cacao_workdir / f'setupfiles/{conf}/conf/wfsrefc.fits')
        self._update_fits(
            data,
            config.AO.cacao_workdir / f'setupfiles/{conf}/conf/wfsmask.fits')
        self._update_fits(
            data,
            config.AO.cacao_workdir / f'setupfiles/{conf}/conf/wfsmap.fits')
        self._update_fits(
            data, config.AO.cacao_workdir /
            f'setupfiles/{conf}/conf/CMmodesWFS.fits')
        self._update_fits(
            data,
            config.AO.cacao_workdir / f'setupfiles/{conf}/conf/dmmask.fits')
        self._update_fits(
            data,
            config.AO.cacao_workdir / f'setupfiles/{conf}/conf/dmmap.fits')
        self._update_fits(
            data,
            config.AO.cacao_workdir / f'setupfiles/{conf}/conf/CMmodesDM.fits')

        self._update_stream(data, f'aol{loop}_wfsref')
        self._update_stream(data, f'aol{loop}_wfsrefc')
        self._update_stream(data, f'aol{loop}_wfsmask')
        self._update_stream(data, f'aol{loop}_wfsmap')
        self._update_stream(data, f'aol{loop}_modesWFS')
        self._update_stream(data, f'aol{loop}_dmmask')
        self._update_stream(data, f'aol{loop}_dmmap')
        self._update_stream(data, f'aol{loop}_DMmodes')

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

    def set_plc_shutter_state(self, state):
        shutter._switch(state)

    def set_plc_flipmirror_position(self, position):
        flip_mirror._switch(position)

    def set_plc_calibunit_position(self, position):
        calib_unit.move(position)

    def set_plc_tungsten_state(self, state):
        tungsten.send_command(state)

    def set_plc_laser_state(self, state):
        laser._switch(state)

    def set_plc_laser_intensity(self, intensity):
        laser.set_intensity(intensity)

    def set_plc_filterwheel_filter(self, filter):
        filterwheel.set_filter(filter)

    def set_plc_adc_1_position(self, position):
        adc.rotate(1, position)

    def set_plc_adc_2_position(self, position):
        adc.rotate(2, position)

    def set_fli_image(self, exposure_time):
        camera.take_frame(exposure_time)

    def get_fli_cancel(self):
        camera.cancel()

    def get_ippower_rtc_on(self):
        ippower.switch(config.IPPower.Port.RTC, IPPowerStatus.ON)

    def get_ippower_rtc_off(self):
        ippower.switch(config.IPPower.Port.RTC, IPPowerStatus.OFF)

    def get_ippower_bench_on(self):
        ippower.switch(config.IPPower.Port.Bench, IPPowerStatus.ON)

    def get_ippower_bench_off(self):
        ippower.switch(config.IPPower.Port.Bench, IPPowerStatus.OFF)

    def get_ippower_dm_on(self):
        ippower.switch(config.IPPower.Port.BMC_DM, IPPowerStatus.ON)

    def get_ippower_dm_off(self):
        ippower.switch(config.IPPower.Port.BMC_DM, IPPowerStatus.OFF)

    def get_centering_star(self):
        centering.center_on_target()

    def get_centering_laser(self):
        centering.center_on_laser()

    def set_services_action(self, unit, action):
        services.unit_control(unit, action)

    ##### DM channels

    def reset_dm(self, dm_number):
        aocontrol.reset_dm(dm_number)

    def reset_channel(self, dm_number, channel):
        aocontrol.reset_channel(dm_number, channel)

    ##### DM & TTM control

    def set_dm_to(self, array):
        stream = toolbox.open_stream_once(config.Streams.DM_USER_CONTROLLED,
                                          self.streams_and_fps_cache)
        if stream is not None:
            stream.set_data(array, True)

    def set_ttm_to(self, array):
        stream = toolbox.open_stream_once(config.Streams.TTM_USER_CONTROLLED,
                                          self.streams_and_fps_cache)
        if stream is not None:
            stream.set_data(array, True)

    ##### Logs

    def get_logs_init(self):
        entries = []
        for entry in logs.seek(self.reader, LogsOutputType.QT,
                               config.GUI.initial_logs_entries):
            entry['text'] = '<span class="init">' + entry['text'] + '<span>'

            entries.append(entry)

        return entries

    def get_logs_new(self):
        entries = []

        for entry in logs.get_last_entries(self.reader, LogsOutputType.QT):
            entries.append(entry)

        return entries
