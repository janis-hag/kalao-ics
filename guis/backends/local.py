from datetime import datetime, timezone
from pathlib import Path

from astropy.io import fits

from kalao import database, ippower, logs, services
from kalao.cacao import aocontrol, toolbox
from kalao.fli import camera
from kalao.plc import (adc, calibunit, filterwheel, flipmirror, laser,
                       plc_utils, shutter, temperature_control, tungsten)
from kalao.sequencer import centering, focusing

from guis.backends.abstract import AbstractBackend, timeit

from kalao.definitions.enums import IPPowerStatus

import config


class SHMFPSBackend(AbstractBackend):
    def _update_stream(self, data, stream_name, key=None):
        if key is None:
            key = stream_name

        stream = toolbox.open_stream_once(stream_name)

        if stream is None:
            return

        if key not in data:
            data[key] = {}

        data[key].update({
            'cnt0': stream.IMAGE.md.cnt0,
            'data': stream.get_data(check=False),
        })

    def _update_stream_keywords(self, data, stream_name):
        stream = toolbox.open_stream_once(stream_name)

        if stream is None:
            return

        if stream_name not in data:
            data[stream_name] = {}

        data[stream_name]['keywords'] = stream.get_keywords()

    def _update_stream_cnt(self, data, stream_name):
        stream = toolbox.open_stream_once(stream_name)

        if stream is None:
            return

        if data.get(stream_name) is None:
            data[stream_name] = {}

        data[stream_name]['cnt0'] = stream.IMAGE.md.cnt0,

    def _update_param(self, data, fps_name, param_name):
        if fps_name not in data:
            data[fps_name] = {}

        fps = toolbox.open_fps_once(fps_name)

        if fps is None:
            return

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

        if not fits_file.exists():
            return

        data[key] = {
            'mtime':
                datetime.fromtimestamp(fits_file.stat().st_mtime,
                                       tz=timezone.utc),
            'data':
                fits.getdata(fits_file),
        }

    def _update_fits_full(self, data, fits_file):
        fits_file = Path(fits_file)
        key = fits_file.stem

        if not fits_file.exists():
            return

        data[key] = {
            'mtime':
                datetime.fromtimestamp(fits_file.stat().st_mtime,
                                       tz=timezone.utc),
            'hdul':
                fits.open(fits_file)
        }


class MainBackend(SHMFPSBackend):
    def __init__(self):
        super().__init__()

        self.reader = logs.get_reader(True)

    @timeit
    def get_streams_all(self):
        data = {}

        self._update_stream(data, config.Streams.DM)
        self._update_param(data, config.FPS.BMC, 'max_stroke')

        self._update_stream(data, config.Streams.NUVU)

        self._update_stream(data, config.Streams.SLOPES)
        self._update_param(data, config.FPS.SHWFS, 'slope_x_avg')
        self._update_param(data, config.FPS.SHWFS, 'slope_y_avg')
        self._update_param(data, config.FPS.SHWFS, 'residual_rms')

        self._update_stream(data, config.Streams.FLUX)
        self._update_param(data, config.FPS.SHWFS, 'flux_avg')
        self._update_param(data, config.FPS.SHWFS, 'flux_max')

        if self._emit:
            self.streams_all_updated.emit(data)
        return data

    @timeit
    def get_streams_fli(self):
        data = {}

        self._update_stream(data, config.Streams.FLI)
        self._update_stream_keywords(data, config.Streams.FLI)

        if self._emit:
            self.streams_fli_updated.emit(data)
        return data

    @timeit
    def get_all(self):
        data = {}

        self._update_stream_cnt(data, config.Streams.FLI)

        self._update_stream(data, config.Streams.TTM)
        self._update_stream(data, config.Streams.MODALGAINS)

        self._update_param(data, config.FPS.NUVU, 'autogain_on')
        self._update_param(data, config.FPS.NUVU, 'autogain_setting')

        self._update_param(data, config.FPS.BMC, 'max_stroke')
        self._update_param(data, config.FPS.BMC, 'stroke_mode')

        self._update_param(data, config.FPS.SHWFS, 'algorithm')

        self._update_param(data, config.FPS.DMLOOP, 'loopON')
        self._update_param(data, config.FPS.DMLOOP, 'loopgain')
        self._update_param(data, config.FPS.DMLOOP, 'loopmult')
        self._update_param(data, config.FPS.DMLOOP, 'looplimit')

        self._update_param(data, config.FPS.TTMLOOP, 'loopON')
        self._update_param(data, config.FPS.TTMLOOP, 'loopgain')
        self._update_param(data, config.FPS.TTMLOOP, 'loopmult')
        self._update_param(data, config.FPS.TTMLOOP, 'looplimit')

        self._update_dict(data, 'plc',
                          plc_utils.get_all_status(filter_from_db=True))
        self._update_dict(data, 'services', services.get_all_status())
        self._update_dict(data, 'fli', camera.get_exposure_status())
        self._update_dict(data, 'fli', camera.get_temperatures())
        self._update_dict(data, 'ippower', ippower.status_all())

        self._update_db(
            data, 'obs',
            database.get('obs', ['sequencer_status', 'centering_manual']))

        # Last so it is the closest to timestamp computation
        self._update_stream_keywords(data, config.Streams.NUVU_RAW)

        if self._emit:
            self.all_updated.emit(data)
        return data

    @timeit
    def get_monitoringandtelemetry(self):
        data = {}

        self._update_db(data, 'monitoring',
                        database.get_all_last('monitoring'))
        self._update_db(data, 'telemetry', database.get_all_last('telemetry'))

        self._update_dict(
            data, 'db-timestamps', {
                'monitoring':
                    database.get_collection_last_update('monitoring'),
                'telemetry':
                    database.get_collection_last_update('telemetry'),
            })

        if self._emit:
            self.monitoringandtelemetry_updated.emit(data)
        return data

    @timeit
    def get_streams_dmdisp(self, dm_number):
        data = {}

        self._update_stream(data, f'dm{dm_number:02d}disp')

        for i in range(0, 12):
            self._update_stream(data, f'dm{dm_number:02d}disp{i:02d}')

        if self._emit:
            self.streams_dmdisp_updated.emit(data)
        return data

    @timeit
    def get_focus(self):
        data = {}

        self._update_fits_full(data, config.FITS.last_focus_sequence)

        if self._emit:
            self.focus_updated.emit(data)
        return data

    def set_plots_data(self, since, until, monitoring_keys, telemetry_keys,
                       obs_keys):

        data = {}

        if len(monitoring_keys) > 0:
            data['monitoring'] = database.read_mongo_to_pandas_by_timestamp(
                'monitoring', since, until, monitoring_keys)

        if len(telemetry_keys) > 0:
            data['telemetry'] = database.read_mongo_to_pandas_by_timestamp(
                'telemetry', since, until, telemetry_keys)

        if len(obs_keys) > 0:
            data['obs'] = database.read_mongo_to_pandas_by_timestamp(
                'obs', since, until, obs_keys)

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

    ##### FLI Zoom

    def set_centering_manual(self, x, y):
        centering.manual_centering(x, y)

    def get_centering_validate(self):
        centering.validate_manual_centering()

    ##### Loop controls

    # DM Loop

    def set_dmloop_on(self, state):
        aocontrol.switch_loop(config.AO.DM_loop_number, state)

    def set_dmloop_gain(selfself, gain):
        aocontrol.set_dmloop_gain(gain)

    def set_dmloop_mult(selfself, mult):
        aocontrol.set_dmloop_mult(mult)

    def set_dmloop_limit(selfself, limit):
        aocontrol.set_dmloop_limit(limit)

    # TTM Loop

    def set_ttmloop_on(self, state):
        aocontrol.switch_loop(config.AO.TTM_loop_number, state)

    def set_ttmloop_gain(selfself, gain):
        aocontrol.set_ttmloop_gain(gain)

    def set_ttmloop_mult(selfself, mult):
        aocontrol.set_ttmloop_mult(mult)

    def set_ttmloop_limit(selfself, limit):
        aocontrol.set_ttmloop_limit(limit)

    # Wavefront Sensor

    def set_nuvu_emgain(self, emgain):
        aocontrol.set_emgain(emgain)

    def set_nuvu_exposuretime(self, exposuretime):
        aocontrol.set_exptime(exposuretime)

    def set_nuvu_autogain_on(self, state):
        aocontrol.switch_autogain(state)

    def set_nuvu_autogain_setting(self, setting):
        aocontrol.set_autogain_setting(setting)

    def set_modalgains(self, modalgains):
        aocontrol.set_modalgains(modalgains)

    # Deformable Mirror

    def set_bmc_maxstroke(self, stroke):
        aocontrol.set_bmc_max_stroke(stroke)

    def set_bmc_strokemode(self, mode):
        aocontrol.set_bmc_stroke_mode(mode)

    ##### Engineering

    def set_plc_shutter_state(self, state):
        shutter._switch(state)

    def get_plc_shutter_init(self):
        shutter.init(force_init=True)

    def set_plc_flipmirror_position(self, position):
        flipmirror._switch(position)

    def get_plc_flipmirror_init(self):
        flipmirror.init(force_init=True)

    def set_plc_calibunit_position(self, position):
        calibunit.move(position)

    def get_plc_calibunit_init(self):
        calibunit.init(force_init=True)

    def get_plc_calibunit_stop(self):
        calibunit.stop()

    def get_plc_calibunit_laser(self):
        calibunit.move_to_laser_position()

    def get_plc_calibunit_tungsten(self):
        calibunit.move_to_tungsten_position()

    def set_plc_tungsten_state(self, state):
        if state:
            tungsten.on()
        else:
            tungsten.off()

    def get_plc_tungsten_init(self):
        tungsten.init(force_init=True)

    def set_plc_laser_state(self, state):
        if state:
            laser.enable()
        else:
            laser.disable()

    def set_plc_laser_power(self, power):
        laser.set_power(power)

    def get_plc_laser_init(self):
        laser.init(force_init=True)

    def get_plc_lamps_off(self):
        plc_utils.lamps_off()

    def set_plc_filterwheel_filter(self, filter):
        filterwheel.set_filter(filter)

    def get_plc_filterwheel_init(self):
        filterwheel.init(force_init=True)

    def set_plc_adc_1_angle(self, position):
        adc.rotate(config.PLC.Node.ADC1, position)

    def get_plc_adc1_init(self):
        adc.init(config.PLC.Node.ADC1, force_init=True)

    def get_plc_adc1_stop(self):
        adc.stop(config.PLC.Node.ADC1)

    def set_plc_adc_2_angle(self, position):
        adc.rotate(config.PLC.Node.ADC2, position)

    def get_plc_adc2_init(self):
        adc.init(config.PLC.Node.ADC2, force_init=True)

    def get_plc_adc2_stop(self):
        adc.stop(config.PLC.Node.ADC2)

    def get_plc_adc_zerodisp(self):
        adc.set_zero_disp()

    def get_plc_adc_maxdisp(self):
        adc.set_max_disp()

    def set_plc_pump_state(self, state):
        if state:
            temperature_control.pump_on()
        else:
            temperature_control.pump_off()

    def set_plc_fan_state(self, state):
        if state:
            temperature_control.fan_on()
        else:
            temperature_control.fan_off()

    def set_plc_heater_state(self, state):
        if state:
            temperature_control.heater_on()
        else:
            temperature_control.heater_off()

    def set_fli_image(self, exposure_time, frames):
        if frames == 1:
            camera.take_frame(exposure_time)
        else:
            camera.take_cube(frames, dit=exposure_time)

    def get_fli_cancel(self):
        camera.cancel()

    def get_nuvu_acquisition_start(self):
        aocontrol.start_wfs_acquisition()

    def get_nuvu_acquisition_stop(self):
        aocontrol.stop_wfs_acquisition()

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

    def set_channels_resetall(self, dm_number):
        aocontrol.reset_dm(dm_number)

    def set_channels_reset(self, dm_number, channel):
        aocontrol.reset_channel(dm_number, channel)

    ##### DM & TTM control

    def set_dm_pattern(self, array):
        stream = toolbox.open_stream_once(config.Streams.DM_USER_CONTROLLED)
        if stream is not None:
            stream.set_data(array, True)

    def set_ttm_pattern(self, array):
        stream = toolbox.open_stream_once(config.Streams.TTM_USER_CONTROLLED)
        if stream is not None:
            stream.set_data(array, True)

    ##### Focusing

    def get_focus_autofocus(self):
        focusing.autofocus()

    def get_focus_sequence(self):
        focusing.focus_sequence()

    ##### Logs

    def get_logs_init(self):
        return logs.seek(self.reader,
                         entries_number=config.GUI.logs_initial_entries)

    def get_logs_new(self):
        return logs.get_last_entries(self.reader)

    def get_logs_between(self, since, until):
        return logs.get_entries_between(self.reader, since, until)
