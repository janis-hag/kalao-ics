import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from astropy.io import fits

from kalao import database, ippower, logs, services
from kalao.cacao import aocontrol, toolbox
from kalao.hardware import (adc, calibunit, camera, cooling, filterwheel,
                            flipmirror, hw_utils, laser, shutter, tungsten,
                            wfs)
from kalao.rtc import rtc
from kalao.sequencer import centering, focusing

import libtmux

from guis.backends.abstract import AbstractBackend, emit, timeit

from kalao.definitions.enums import IPPowerStatus, LoopStatus, ObservationType

import config


class SHMFPSBackend(AbstractBackend):
    def _update_shm(self, data, shm_name, key=None):
        if key is None:
            key = shm_name

        shm = toolbox.open_shm_once(shm_name)

        if shm is None:
            return

        if key not in data:
            data[key] = {}

        data[key].update({
            'cnt0': shm.IMAGE.md.cnt0,
            'data': shm.get_data(check=False),
        })

    def _update_shm_keywords(self, data, shm_name):
        shm = toolbox.open_shm_once(shm_name)

        if shm is None:
            return

        if shm_name not in data:
            data[shm_name] = {}

        data[shm_name]['keywords'] = shm.get_keywords()

    def _update_shm_state(self, data, shm_name):
        shm = toolbox.open_shm_once(shm_name)

        if shm_name not in data:
            data[shm_name] = {}

        if shm is None:
            data[shm_name]['state'] = 'M'
        else:
            data[shm_name]['state'] = 'E'

    def _update_shm_md(self, data, shm_name):
        shm = toolbox.open_shm_once(shm_name)

        if shm is None:
            return

        if shm_name not in data:
            data[shm_name] = {}

        data[shm_name]['md'] = {
            'shape': shm.shape,
            'cnt0': shm.IMAGE.md.cnt0,
            'creationtime': shm.IMAGE.md.creationtime,
            'acqtime': shm.IMAGE.md.acqtime,
        }

    def _update_fps_param(self, data, fps_name, param_name):
        fps = toolbox.open_fps_once(fps_name)

        if fps is None:
            return

        if fps_name not in data:
            data[fps_name] = {}

        data[fps_name][param_name] = fps.get_param(param_name)

    def _update_fps_state(self, data, fps_name):
        fps = toolbox.open_fps_once(fps_name)

        if fps_name not in data:
            data[fps_name] = {}

        if fps is None:
            data[fps_name]['state'] = 'M'

        else:
            data[fps_name]['state'] = ''

            if fps.conf_isrunning():
                data[fps_name]['state'] += 'C'

            if fps.run_isrunning():
                data[fps_name]['state'] += 'R'

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

    def version(self):
        return config.version

    @emit
    @timeit
    def streams_all(self):
        data = {}

        self._update_shm(data, config.SHM.DM)
        self._update_fps_param(data, config.FPS.BMC, 'max_stroke')

        self._update_shm(data, config.SHM.NUVU)

        self._update_shm(data, config.SHM.SLOPES)
        self._update_fps_param(data, config.FPS.SHWFS, 'slope_x_avg')
        self._update_fps_param(data, config.FPS.SHWFS, 'slope_y_avg')
        self._update_fps_param(data, config.FPS.SHWFS, 'residual_rms')

        self._update_shm(data, config.SHM.FLUX)
        self._update_fps_param(data, config.FPS.SHWFS, 'flux_avg')
        self._update_fps_param(data, config.FPS.SHWFS, 'flux_max')

        self._update_shm(data, config.SHM.MODE_COEFFS)

        return data

    @emit
    @timeit
    def camera_image(self):
        data = {}

        self._update_fits_full(data, config.FITS.last_image_all)

        return data

    @emit
    @timeit
    def all(self):
        data = {}

        self._update_fits_mtime(data, config.FITS.last_image_all)

        self._update_shm(data, config.SHM.TTM)
        self._update_shm(data, config.SHM.MODALGAINS)

        self._update_fps_param(data, config.FPS.NUVU, 'autogain_on')
        self._update_fps_param(data, config.FPS.NUVU, 'autogain_setting')

        self._update_fps_param(data, config.FPS.BMC, 'max_stroke')
        self._update_fps_param(data, config.FPS.BMC, 'stroke_mode')
        self._update_fps_param(data, config.FPS.BMC, 'target_stroke')

        self._update_fps_param(data, config.FPS.SHWFS, 'algorithm')

        self._update_fps_param(data, config.FPS.DMLOOP, 'loopON')
        self._update_fps_param(data, config.FPS.DMLOOP, 'loopgain')
        self._update_fps_param(data, config.FPS.DMLOOP, 'loopmult')
        self._update_fps_param(data, config.FPS.DMLOOP, 'looplimit')

        self._update_fps_param(data, config.FPS.TTMLOOP, 'loopON')
        self._update_fps_param(data, config.FPS.TTMLOOP, 'loopgain')
        self._update_fps_param(data, config.FPS.TTMLOOP, 'loopmult')
        self._update_fps_param(data, config.FPS.TTMLOOP, 'looplimit')

        self._update_fps_param(data, config.FPS.CONFIG, 'adc_synchronisation')
        self._update_fps_param(data, config.FPS.CONFIG, 'ttm_offloading')

        self._update_dict(data, 'plc',
                          hw_utils.get_all_status(filter_from_db=True))
        self._update_dict(data, 'services', services.get_all_status())
        self._update_dict(
            data, 'camera', {
                'camera_server_status': camera.server_status(),
                'camera_status': camera.get_camera_status()
            })
        self._update_dict(data, 'camera', camera.get_exposure_status())
        self._update_dict(data, 'camera', camera.get_temperatures())
        self._update_dict(data, 'ippower', ippower.status_all())

        tmux_server = libtmux.Server()
        self._update_dict(
            data, 'tmux', {
                'tmux_server_alive':
                    tmux_server.is_alive(),
                'tmux_sessions':
                    [session.name for session in tmux_server.sessions]
            })

        for proc in config.AO.procs:
            self._update_fps_state(data, proc)

        for stream in config.AO.streams:
            self._update_shm_state(data, stream)
            self._update_shm_md(data, stream)

        self._update_db(
            data, 'obs',
            database.get_all_last('obs',
                                  ['sequencer_status', 'centering_manual']))

        self._update_shm(data, config.SHM.TELEMETRY_TTM)

        # Last so it is the closest to timestamp computation
        self._update_shm_keywords(data, config.SHM.NUVU_RAW)

        return data

    @emit
    @timeit
    def monitoring(self):
        data = {}

        self._update_db(data, 'monitoring',
                        database.get_all_last('monitoring'))

        self._update_dict(data, 'db-timestamps', {
            'monitoring': database.get_collection_last_update('monitoring'),
        })

        return data

    @emit
    @timeit
    def streams_channels_dm(self):
        data = {}

        self._update_shm(data, config.SHM.DM)

        for i in range(0, 12):
            self._update_shm(data, f'{config.SHM.DM}{i:02d}')

        return data

    @emit
    @timeit
    def streams_channels_ttm(self):
        data = {}

        self._update_shm(data, config.SHM.TTM)

        for i in range(0, 12):
            self._update_shm(data, f'{config.SHM.TTM}{i:02d}')

        return data

    @emit
    @timeit
    def focus_sequence(self):
        data = {}

        self._update_fits_full(data, config.FITS.last_focus_sequence)

        return data

    def plots_data(self, *, since, until, monitoring_keys, obs_keys):

        data = {}

        if len(monitoring_keys) > 0:
            data['monitoring'] = database.read_mongo_to_pandas(
                'monitoring', keys=monitoring_keys, since=since, until=until)

        if len(obs_keys) > 0:
            data['obs'] = database.read_mongo_to_pandas(
                'obs', keys=obs_keys, since=since, until=until)

        return data

    def calibration_ready(self, *, conf, loop):
        if not wfs.acquisition_running():
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

    def calibration_data(self, *, conf, loop):
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

        self._update_shm(data, f'aol{loop}_wfsref')
        self._update_shm(data, f'aol{loop}_wfsrefc')
        self._update_shm(data, f'aol{loop}_wfsmask')
        self._update_shm(data, f'aol{loop}_wfsmap')
        self._update_shm(data, f'aol{loop}_modesWFS')
        self._update_shm(data, f'aol{loop}_dmmask')
        self._update_shm(data, f'aol{loop}_dmmap')
        self._update_shm(data, f'aol{loop}_DMmodes')

        return data

    def calibration_reload(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/apply-calib-saved.sh'

        res = subprocess.run([script], timeout=60, capture_output=True,
                             cwd=config.AO.cacao_workdir)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def calibration_prepare(self, *, conf, loop):
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

    def calibration_mlat(self, *, conf, loop):
        data = {}

        ready_data = self.calibration_ready(conf=conf, loop=loop)
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

        self._update_fps_param(data, f'mlat-{loop}', 'out.framerateHz')
        self._update_fps_param(data, f'mlat-{loop}', 'out.latencyfr')

        data['hardwlatencypts'] = np.loadtxt(
            config.AO.cacao_workdir /
            f'KalAO-{conf}-rootdir/rundir/fps.mlat-{loop}.datadir/hardwlatencypts.dat'
        )

        return data

    def calibration_mkDMpokemodes(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/01-mkDMpokemodes.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def calibration_takeref(self, *, conf, loop):
        data = {}

        ready_data = self.calibration_ready(conf=conf, loop=loop)
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

    def calibration_acqlinResp(self, *, conf, loop):
        data = {}

        ready_data = self.calibration_ready(conf=conf, loop=loop)
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

    def calibration_RMHdecode(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/04-RMHdecode.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        self._update_fits(
            data, config.AO.cacao_workdir /
            f'KalAO-{conf}-rootdir/conf/RMmodesWFS/zrespM-H.fits')

        return data

    def calibration_RMmkmask(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/05-RMmkmask.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def calibration_compCM(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/06-compCM.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def calibration_load(self, *, conf, loop):
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/apply-calib-rootdir.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode()

        return data

    def calibration_save(self, *, conf, loop, comment):
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

    ##### Science Camera

    def centering_manual(self, *, dx, dy):
        centering.manual_centering(dx, dy)

    def centering_validate(self):
        centering.validate_manual_centering()

    ##### Loop controls

    # DM Loop

    def loops_dm_on(self, *, state):
        aocontrol.switch_loop(config.AO.DM_loop_number, state,
                              with_autogain=False, autozero=False)

    def loops_dm_gain(self, *, gain):
        aocontrol.set_dmloop_gain(gain)

    def loops_dm_mult(self, *, mult):
        aocontrol.set_dmloop_mult(mult)

    def loops_dm_limit(self, *, limit):
        aocontrol.set_dmloop_limit(limit)

    def loops_dm_zero(self):
        aocontrol.dmloop_zero()

    # TTM Loop

    def loops_ttm_on(self, *, state):
        aocontrol.switch_loop(config.AO.TTM_loop_number, state,
                              with_autogain=False, autozero=False)

    def loops_ttm_gain(self, *, gain):
        aocontrol.set_ttmloop_gain(gain)

    def loops_ttm_mult(self, *, mult):
        aocontrol.set_ttmloop_mult(mult)

    def loops_ttm_limit(self, *, limit):
        aocontrol.set_ttmloop_limit(limit)

    def loops_ttm_zero(self):
        aocontrol.ttmloop_zero()

    # Wavefront Sensor

    def wfs_emgain(self, *, emgain):
        aocontrol.set_emgain(emgain)

    def wfs_exposuretime(self, *, exposuretime):
        aocontrol.set_exptime(exposuretime)

    def wfs_autogain_on(self, *, state):
        aocontrol.switch_autogain(state)

    def wfs_autogain_setting(self, *, setting):
        aocontrol.set_autogain_setting(setting)

    # Deformable Mirror

    def dm_maxstroke(self, *, stroke):
        aocontrol.set_dm_max_stroke(stroke)

    def dm_strokemode(self, *, mode):
        aocontrol.set_dm_stroke_mode(mode)

    def dm_targetstroke(self, *, target):
        aocontrol.set_dm_target_stroke(target)

    # Observation

    def adc_synchronisation(self, *, state):
        toolbox.set_fps_value(config.FPS.CONFIG, 'adc_synchronisation', state)

    def ttm_offloading(self, *, state):
        toolbox.set_fps_value(config.FPS.CONFIG, 'ttm_offloading', state)

    # Modal gains

    def loops_dm_modalgains(self, *, modalgains):
        aocontrol.set_modalgains(modalgains)

    ##### Engineering

    def plc_shutter_state(self, *, state):
        shutter._switch(state)

    def plc_shutter_init(self):
        shutter.init()

    def plc_flipmirror_position(self, *, position):
        flipmirror._switch(position)

    def plc_flipmirror_init(self):
        flipmirror.init()

    def plc_calibunit_position(self, *, position):
        calibunit.move(position)

    def plc_calibunit_init(self):
        calibunit.init(force_init=True)

    def plc_calibunit_stop(self):
        calibunit.stop()

    def plc_calibunit_laser(self):
        calibunit.move_to_laser_position()

    def plc_calibunit_tungsten(self):
        calibunit.move_to_tungsten_position()

    def plc_tungsten_state(self, *, state):
        if state:
            tungsten.on()
        else:
            tungsten.off()

    def plc_tungsten_init(self):
        tungsten.init()

    def plc_laser_state(self, *, state):
        if state:
            laser.enable()
        else:
            laser.disable()

    def plc_laser_power(self, *, power):
        laser.set_power(power)

    def plc_laser_init(self):
        laser.init()

    def plc_lamps_off(self):
        hw_utils.lamps_off()

    def plc_filterwheel_filter(self, *, filter):
        filterwheel.set_filter(filter)

    def plc_filterwheel_init(self):
        filterwheel.init()

    def plc_adc1_angle(self, *, position):
        adc.rotate(config.PLC.Node.ADC1, position)

    def plc_adc1_init(self):
        adc.init(config.PLC.Node.ADC1, force_init=True)

    def plc_adc1_stop(self):
        adc.stop(config.PLC.Node.ADC1)

    def plc_adc2_angle(self, *, position):
        adc.rotate(config.PLC.Node.ADC2, position)

    def plc_adc2_init(self):
        adc.init(config.PLC.Node.ADC2, force_init=True)

    def plc_adc2_stop(self):
        adc.stop(config.PLC.Node.ADC2)

    def plc_adc_zerodisp(self):
        adc.set_zero_disp()

    def plc_adc_maxdisp(self):
        adc.set_max_disp()

    def plc_adc_angleoffset(self, *, angle, offset):
        adc.set_angle(angle, offset)

    def plc_pump_state(self, *, state):
        if state:
            cooling.pump_on()
        else:
            cooling.pump_off()

    def plc_fan_state(self, *, state):
        if state:
            cooling.heatexchanger_fan_on()
        else:
            cooling.heatexchanger_fan_off()

    def plc_heater_state(self, *, state):
        if state:
            cooling.heater_on()
        else:
            cooling.heater_off()

    def camera_take(self, *, exposure_time, frames, roi_size):
        camera.take_image(ObservationType.ENGINEERING, exptime=exposure_time,
                          nbframes=frames, roi_size=roi_size)

    def camera_cancel(self):
        camera.cancel()

    def wfs_acquisition_start(self):
        wfs.start_acquisition()

    def wfs_acquisition_stop(self):
        wfs.stop_acquisition()

    def ippower_rtc_on(self):
        ippower.switch(config.IPPower.Port.RTC, IPPowerStatus.ON)

    def ippower_rtc_off(self):
        ippower.switch(config.IPPower.Port.RTC, IPPowerStatus.OFF)

    def ippower_bench_on(self):
        ippower.switch(config.IPPower.Port.Bench, IPPowerStatus.ON)

    def ippower_bench_off(self):
        ippower.switch(config.IPPower.Port.Bench, IPPowerStatus.OFF)

    def ippower_dm_on(self):
        ippower.switch(config.IPPower.Port.DM, IPPowerStatus.ON)

    def ippower_dm_off(self):
        ippower.switch(config.IPPower.Port.DM, IPPowerStatus.OFF)

    def centering_laser(self):
        centering.center_on_laser()

    def services_action(self, *, unit, action):
        services.unit_control(unit, action)

    def deadman(self, *, count):
        database.store('obs', {'deadman_keepalive': count})

    ##### DM channels

    def channels_resetall(self, *, dm_number):
        aocontrol.reset_dm(dm_number)

    def channels_reset(self, *, dm_number, channel):
        aocontrol.reset_channel(dm_number, channel)

    ##### DM & TTM control

    def dm_pattern(self, *, pattern):
        shm = toolbox.open_shm_once(config.SHM.DM_USER_CONTROLLED)
        if shm is not None:
            shm.set_data(pattern, True)

    def ttm_position(self, *, tip, tilt):
        shm = toolbox.open_shm_once(config.SHM.TTM_USER_CONTROLLED)
        if shm is not None:
            shm.set_data(np.array([tip, tilt]), True)

    ##### Focusing

    def focus_autofocus(self):
        focusing.autofocus()

    ##### Logs

    def logs_init(self):
        return logs.seek(self.reader,
                         entries_number=config.GUI.logs_initial_entries)

    def logs_new(self):
        return logs.get_last_entries(self.reader)

    def logs_between(self, *, since, until):
        return logs.get_entries_between(since, until)

    ##### Instrument

    def shutdown(self, *, iknowwhatimdoing):
        if iknowwhatimdoing == 'yes':
            return rtc.shutdown_sequence()
        else:
            return None
