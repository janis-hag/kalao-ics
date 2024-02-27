import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from astropy.io import fits

from kalao import database, ippower, logs, services
from kalao.cacao import aocontrol, toolbox
from kalao.fli import camera
from kalao.plc import (adc, calibunit, filterwheel, flipmirror, laser,
                       plc_utils, shutter, temperature_control, tungsten)
from kalao.sequencer import centering, focusing

from guis.backends.abstract import AbstractBackend, emit, timeit

from kalao.definitions.enums import IPPowerStatus, LoopStatus, ObservationType

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
        if not isinstance(fits_file, Path):
            fits_file = Path(fits_file)

        key = fits_file.stem

        try:
            data[key] = {
                'mtime':
                    datetime.fromtimestamp(fits_file.stat().st_mtime,
                                           tz=timezone.utc),
                'data':
                    fits.getdata(fits_file),
            }
        except (FileNotFoundError, OSError):
            pass

    def _update_fits_full(self, data, fits_file):
        if not isinstance(fits_file, Path):
            fits_file = Path(fits_file)

        key = fits_file.stem

        try:
            # Recreate HDU List to avoid "cannot pickle '_io.BufferedReader' object" error
            hdul = fits.open(fits_file)
            hdul_ = fits.HDUList()

            for hdu in hdul:
                hdu_ = type(hdu)()
                hdu_.data = hdu.data
                hdu_.header = hdu.header
                hdul_.append(hdu_)

            data[key] = {
                'mtime':
                    datetime.fromtimestamp(fits_file.stat().st_mtime,
                                           tz=timezone.utc),
                'hdul':
                    hdul_,
            }
        except (FileNotFoundError, OSError):
            pass

    def _update_fits_mtime(self, data, fits_file):
        if not isinstance(fits_file, Path):
            fits_file = Path(fits_file)

        key = fits_file.stem

        try:
            if data.get(key) is None:
                data[key] = {}

            data[key]['mtime'] = datetime.fromtimestamp(
                fits_file.stat().st_mtime, tz=timezone.utc)
        except (FileNotFoundError, OSError):
            pass


class MainBackend(SHMFPSBackend):
    def __init__(self):
        super().__init__()

        self.reader = logs.get_reader(True)

    @emit('streams_all_updated')
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

        self._update_stream(data, config.Streams.MODE_COEFFS)

        return data

    @emit('fli_image_updated')
    @timeit
    def get_fli_image(self):
        data = {}

        self._update_fits_full(data, config.FITS.last_image_all)

        return data

    @emit('all_updated')
    @timeit
    def get_all(self):
        data = {}

        self._update_fits_mtime(data, config.FITS.last_image_all)

        self._update_stream(data, config.Streams.TTM)
        self._update_stream(data, config.Streams.MODALGAINS)

        self._update_param(data, config.FPS.NUVU, 'autogain_on')
        self._update_param(data, config.FPS.NUVU, 'autogain_setting')

        self._update_param(data, config.FPS.BMC, 'max_stroke')
        self._update_param(data, config.FPS.BMC, 'stroke_mode')
        self._update_param(data, config.FPS.BMC, 'target_stroke')

        self._update_param(data, config.FPS.SHWFS, 'algorithm')

        self._update_param(data, config.FPS.DMLOOP, 'loopON')
        self._update_param(data, config.FPS.DMLOOP, 'loopgain')
        self._update_param(data, config.FPS.DMLOOP, 'loopmult')
        self._update_param(data, config.FPS.DMLOOP, 'looplimit')

        self._update_param(data, config.FPS.TTMLOOP, 'loopON')
        self._update_param(data, config.FPS.TTMLOOP, 'loopgain')
        self._update_param(data, config.FPS.TTMLOOP, 'loopmult')
        self._update_param(data, config.FPS.TTMLOOP, 'looplimit')

        self._update_param(data, config.FPS.CONFIG, 'adc_update')
        self._update_param(data, config.FPS.CONFIG, 'ttm_offload')

        self._update_dict(data, 'plc',
                          plc_utils.get_all_status(filter_from_db=True))
        self._update_dict(data, 'services', services.get_all_status())
        self._update_dict(data, 'fli', camera.get_exposure_status())
        self._update_dict(data, 'fli', camera.get_temperatures())
        self._update_dict(data, 'ippower', ippower.status_all())

        self._update_db(
            data, 'obs',
            database.get('obs', ['sequencer_status', 'centering_manual']))

        self._update_stream(data, config.Streams.TELEMETRY_TTM)

        # Last so it is the closest to timestamp computation
        self._update_stream_keywords(data, config.Streams.NUVU_RAW)

        return data

    @emit('monitoringandtelemetry_updated')
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

        return data

    @emit('streams_channels_dm_updated')
    @timeit
    def get_streams_channels_dm(self):
        data = {}

        self._update_stream(data, config.Streams.DM)

        for i in range(0, 12):
            self._update_stream(data, f'{config.Streams.DM}{i:02d}')

        return data

    @emit('streams_channels_ttm_updated')
    @timeit
    def get_streams_channels_ttm(self):
        data = {}

        self._update_stream(data, config.Streams.TTM)

        for i in range(0, 12):
            self._update_stream(data, f'{config.Streams.TTM}{i:02d}')

        return data

    @emit('focus_sequence_updated')
    @timeit
    def get_focus_sequence(self):
        data = {}

        self._update_fits_full(data, config.FITS.last_focus_sequence)

        return data

    def set_plots_data(self, *, since, until, monitoring_keys, telemetry_keys,
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

    def get_calibration_ready(self, *, conf, loop):
        if not aocontrol.acquisition_running():
            return {'ready': False, 'reason': 'WFS acquisition is not running'}

        if not aocontrol.check_wfs_flux():
            return {'ready': False, 'reason': 'Not enough flux on WFS'}

        # TODO: check frequency

        loops_status = aocontrol.check_loops()
        if conf == 'ttmloop':
            if LoopStatus.DM_LOOP_ON not in loops_status:
                return {'ready': False, 'reason': 'DM loop is off'}

            if LoopStatus.TTM_LOOP_ON in loops_status:
                return {'ready': False, 'reason': 'TTM loop is on'}
        else:
            if loops_status != LoopStatus.ALL_LOOPS_OFF:
                return {'ready': False, 'reason': 'Both loops should be off'}

        return {'ready': True}

    def set_calibration_data(self, *, conf, loop):
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

    def set_calibration_reload(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/apply-calib-saved.sh'

        res = subprocess.run([script], timeout=60, capture_output=True,
                             cwd=config.AO.cacao_workdir)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def set_latency_measure(self, *, conf, loop):
        data = {}

        ready_data = self.get_calibration_ready(conf, loop)
        if not ready_data['ready']:
            return {
                'returncode':
                    -1,
                'stdout':
                    f'Calibration not ready to run: {ready_data["reason"]}'
            }

        script = config.AO.cacao_workdir / f'scripts/{conf}/00-mlat.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        if res.returncode != 0:
            return data

        self._update_param(data, f'mlat-{loop}', 'out.framerateHz')
        self._update_param(data, f'mlat-{loop}', 'out.latencyfr')

        data['hardwlatencypts'] = np.loadtxt(
            config.AO.cacao_workdir /
            f'KalAO-{conf}-rootdir/rundir/fps.mlat-{loop}.datadir/hardwlatencypts.dat'
        )

        return data

    def set_RMCM_prepare(self, *, conf, loop):
        if conf == 'dmloop':
            if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
                return {'returncode': -1, 'stdout': 'Failed to open loops'}

        elif conf == 'ttmloop':
            if LoopStatus.TTM_LOOP_ON in aocontrol.open_loop(
                    config.AO.TTM_loop_number, with_autogain=False):
                return {'returncode': -1, 'stdout': 'Failed to open TTM loop'}

            if LoopStatus.DM_LOOP_ON not in aocontrol.close_loop(
                    config.AO.DM_loop_number, with_autogain=False):
                return {'returncode': -1, 'stdout': 'Failed to close DM loop'}

            if aocontrol.set_modalgains(np.array([1, 1])) != 0:
                return {
                    'returncode': -1,
                    'stdout': 'Failed to set modal gains'
                }
        else:
            return {'returncode': -1, 'stdout': 'Unknown loop'}

        return {'returncode': 0, 'stdout': 'Success!'}

    def set_RMCM_mkDMpokemodes(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/01-mkDMpokemodes.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def set_RMCM_takeref(self, *, conf, loop):
        data = {}

        ready_data = self.get_calibration_ready(conf, loop)
        if not ready_data['ready']:
            return {
                'returncode':
                    -1,
                'stdout':
                    f'Calibration not ready to run: {ready_data["reason"]}'
            }

        script = config.AO.cacao_workdir / f'scripts/{conf}/02-takeref.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def set_RMCM_acqlinResp(self, *, conf, loop):
        data = {}

        ready_data = self.get_calibration_ready(conf, loop)
        if not ready_data['ready']:
            return {
                'returncode':
                    -1,
                'stdout':
                    f'Calibration not ready to run: {ready_data["reason"]}'
            }

        script = config.AO.cacao_workdir / f'scripts/{conf}/03-acqlinResp.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def set_RMCM_RMHdecode(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/04-RMHdecode.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        self._update_fits(
            data, config.AO.cacao_workdir /
            f'KalAO-{conf}-rootdir/conf/zrespM-H.fits')

        return data

    def set_RMCM_RMmkmask(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/05-RMmkmask.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def set_RMCM_compCM(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/06-compCM.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def set_RMCM_load(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/apply-calib-rootdir.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def set_RMCM_save(self, *, conf, loop, comment):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/save-calib.sh'

        if comment != '':
            args = [script, comment]
        else:
            args = [script]

        res = subprocess.run(args, timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    ##### FLI Zoom

    def set_centering_manual(self, *, x, y):
        centering.manual_centering(x, y)

    def get_centering_validate(self):
        centering.validate_manual_centering()

    ##### Loop controls

    # DM Loop

    def set_dmloop_on(self, *, state):
        aocontrol.switch_loop(config.AO.DM_loop_number, state,
                              with_autogain=False, autozero=False)

    def set_dmloop_gain(selfself, gain):
        aocontrol.set_dmloop_gain(gain)

    def set_dmloop_mult(selfself, mult):
        aocontrol.set_dmloop_mult(mult)

    def set_dmloop_limit(selfself, limit):
        aocontrol.set_dmloop_limit(limit)

    def get_dmloop_zero(self):
        aocontrol.dmloop_zero()

    # TTM Loop

    def set_ttmloop_on(self, *, state):
        aocontrol.switch_loop(config.AO.TTM_loop_number, state,
                              with_autogain=False, autozero=False)

    def set_ttmloop_gain(selfself, gain):
        aocontrol.set_ttmloop_gain(gain)

    def set_ttmloop_mult(selfself, mult):
        aocontrol.set_ttmloop_mult(mult)

    def set_ttmloop_limit(selfself, limit):
        aocontrol.set_ttmloop_limit(limit)

    def get_ttmloop_zero(self):
        aocontrol.ttmloop_zero()

    # Wavefront Sensor

    def set_nuvu_emgain(self, *, emgain):
        aocontrol.set_emgain(emgain)

    def set_nuvu_exposuretime(self, *, exposuretime):
        aocontrol.set_exptime(exposuretime)

    def set_nuvu_autogain_on(self, *, state):
        aocontrol.switch_autogain(state)

    def set_nuvu_autogain_setting(self, *, setting):
        aocontrol.set_autogain_setting(setting)

    # Deformable Mirror

    def set_bmc_maxstroke(self, *, stroke):
        aocontrol.set_bmc_max_stroke(stroke)

    def set_bmc_strokemode(self, *, mode):
        aocontrol.set_bmc_stroke_mode(mode)

    def set_bmc_targetstroke(self, *, target):
        aocontrol.set_bmc_target_stroke(target)

    # Observation

    def set_adc_update(self, *, state):
        aocontrol._set_fps_value(config.FPS.CONFIG, 'adc_update', state)

    def set_ttm_offload(self, *, state):
        aocontrol._set_fps_value(config.FPS.CONFIG, 'ttm_offload', state)

    # Modal gains

    def set_modalgains(self, *, modalgains):
        aocontrol.set_modalgains(modalgains)

    ##### Engineering

    def set_plc_shutter_state(self, *, state):
        shutter._switch(state)

    def get_plc_shutter_init(self):
        shutter.init()

    def set_plc_flipmirror_position(self, *, position):
        flipmirror._switch(position)

    def get_plc_flipmirror_init(self):
        flipmirror.init()

    def set_plc_calibunit_position(self, *, position):
        calibunit.move(position)

    def get_plc_calibunit_init(self):
        calibunit.init(force_init=True)

    def get_plc_calibunit_stop(self):
        calibunit.stop()

    def get_plc_calibunit_laser(self):
        calibunit.move_to_laser_position()

    def get_plc_calibunit_tungsten(self):
        calibunit.move_to_tungsten_position()

    def set_plc_tungsten_state(self, *, state):
        if state:
            tungsten.on()
        else:
            tungsten.off()

    def get_plc_tungsten_init(self):
        tungsten.init()

    def set_plc_laser_state(self, *, state):
        if state:
            laser.enable()
        else:
            laser.disable()

    def set_plc_laser_power(self, *, power):
        laser.set_power(power)

    def get_plc_laser_init(self):
        laser.init()

    def get_plc_lamps_off(self):
        plc_utils.lamps_off()

    def set_plc_filterwheel_filter(self, *, filter):
        filterwheel.set_filter(filter)

    def get_plc_filterwheel_init(self):
        filterwheel.init()

    def set_plc_adc_1_angle(self, *, position):
        adc.rotate(config.PLC.Node.ADC1, position)

    def get_plc_adc1_init(self):
        adc.init(config.PLC.Node.ADC1, force_init=True)

    def get_plc_adc1_stop(self):
        adc.stop(config.PLC.Node.ADC1)

    def set_plc_adc_2_angle(self, *, position):
        adc.rotate(config.PLC.Node.ADC2, position)

    def get_plc_adc2_init(self):
        adc.init(config.PLC.Node.ADC2, force_init=True)

    def get_plc_adc2_stop(self):
        adc.stop(config.PLC.Node.ADC2)

    def get_plc_adc_zerodisp(self):
        adc.set_zero_disp()

    def get_plc_adc_maxdisp(self):
        adc.set_max_disp()

    def set_plc_pump_state(self, *, state):
        if state:
            temperature_control.pump_on()
        else:
            temperature_control.pump_off()

    def set_plc_fan_state(self, *, state):
        if state:
            temperature_control.fan_on()
        else:
            temperature_control.fan_off()

    def set_plc_heater_state(self, *, state):
        if state:
            temperature_control.heater_on()
        else:
            temperature_control.heater_off()

    def set_fli_take(self, *, exposure_time, frames, roi_size):
        camera.take_image(ObservationType.ENGINEERING, exptime=exposure_time,
                          nbframes=frames, roi_size=roi_size)

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

    def get_centering_laser(self):
        centering.center_on_laser()

    def set_services_action(self, *, unit, action):
        services.unit_control(unit, action)

    ##### DM channels

    def set_channels_resetall(self, *, dm_number):
        aocontrol.reset_dm(dm_number)

    def set_channels_reset(self, *, dm_number, channel):
        aocontrol.reset_channel(dm_number, channel)

    ##### DM & TTM control

    def set_dm_pattern(self, *, pattern):
        stream = toolbox.open_stream_once(config.Streams.DM_USER_CONTROLLED)
        if stream is not None:
            stream.set_data(pattern, True)

    def set_ttm_position(self, *, tip, tilt):
        stream = toolbox.open_stream_once(config.Streams.TTM_USER_CONTROLLED)
        if stream is not None:
            stream.set_data(np.array([tip, tilt]), True)

    ##### Focusing

    def get_focus_autofocus(self):
        focusing.autofocus()

    ##### Logs

    def get_logs_init(self):
        return logs.seek(self.reader,
                         entries_number=config.GUI.logs_initial_entries)

    def get_logs_new(self):
        return logs.get_last_entries(self.reader)

    def get_logs_between(self, *, since, until):
        return logs.get_entries_between(since, until)
