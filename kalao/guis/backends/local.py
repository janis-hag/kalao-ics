import subprocess
from datetime import datetime, timezone
from typing import Any

import numpy as np

import libtmux
import requests

from kalao import database, ippower, logs, memory, services
from kalao.cacao import aocontrol
from kalao.hardware import (adc, calibunit, camera, cooling, dm, filterwheel,
                            flipmirror, hw_utils, laser, shutter, ttm,
                            tungsten, wfs)
from kalao.rtc import rtc
from kalao.sequencer import centering, focusing, seq_utils
from kalao.timers import monitoring

from kalao.guis.backends.abstract import SHMFPSBackend, emit, timeit

from kalao.definitions.dataclasses import LogEntry, Template
from kalao.definitions.enums import (FlipMirrorStatus, IPPowerStatus,
                                     LoopStatus, ServiceAction, ShutterStatus,
                                     TemplateID)

import config


class MainBackend(SHMFPSBackend):
    def __init__(self) -> None:
        super().__init__()

    def version(self) -> str:
        return config.version

    @emit
    @timeit
    def streams_all(self) -> dict[str, Any]:
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
    def camera_image(self) -> dict[str, Any]:
        data = {}

        self._update_fits_full(data, config.FITS.last_image_all)

        return data

    @emit
    @timeit
    def all(self) -> dict[str, Any]:
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

        self._update_dict(
            data, 'memory', {
                'sequencer_status':
                    seq_utils.get_sequencer_status(),
                'centering_manual_flag':
                    centering.get_manual_centering_flag(),
                'centering_timeout':
                    memory.hget('centering', 'timeout', type=float,
                                default=np.nan),
                'adc_synchronisation':
                    adc.get_synchronisation(),
                'ttm_offloading':
                    ttm.get_offloading(),
                'gui_window_hint':
                    memory.hget('gui', 'window_hint')
            })

        self._update_dict(data, 'hw',
                          hw_utils.get_all_status(filter_from_memory=True))

        self._update_dict(data, 'services', services.get_all_status())

        self._update_dict(data, 'camera',
                          {'camera_status': camera.get_camera_status()})
        self._update_dict(data, 'camera', camera.get_exposure_status())
        self._update_dict(data, 'camera', camera.get_temperatures())

        self._update_dict(data, 'ippower', ippower.get_all_status())

        tmux_server = libtmux.Server()
        self._update_dict(data, 'tmux', {
            'tmux_sessions':
                [session.name for session in tmux_server.sessions]
        })

        self._update_dict(
            data, 'pgrep', {
                'kalaocam_ctrl':
                    subprocess.run(
                        ['pgrep', '-f', 'camstack.cam_mains.kalaocam'],
                        capture_output=True).returncode,
                'nuvu_fgrab':
                    subprocess.run(['pgrep', '-f', 'hwacq-edttake'],
                                   capture_output=True).returncode,
            })

        for proc in config.AO.processes:
            if proc is None:
                continue

            self._update_fps_md(data, proc)

        for stream in config.AO.streams:
            if stream is None:
                continue

            self._update_shm_md(data, stream)

        self._update_shm(data, config.SHM.TELEMETRY_TTM)

        # Last so it is the closest to timestamp computation
        self._update_shm_keywords(data, config.SHM.NUVU_RAW)

        return data

    @emit
    @timeit
    def monitoring(self) -> dict[str, Any]:
        data = {}

        self._update_db(data, 'monitoring',
                        database.get_all_last('monitoring'))

        self._update_dict(data, 'db-timestamps', {
            'monitoring': database.get_collection_last_update('monitoring'),
        })

        return data

    @emit
    @timeit
    def streams_channels_dm(self) -> dict[str, Any]:
        data = {}

        self._update_shm(data, config.SHM.DM)
        self._update_shm(data, config.SHM.COMMANDS_DM)

        for i in range(0, 12):
            self._update_shm(data, f'{config.SHM.DM}{i:02d}')

        return data

    @emit
    @timeit
    def streams_channels_ttm(self) -> dict[str, Any]:
        data = {}

        self._update_shm(data, config.SHM.TTM)
        self._update_shm(data, config.SHM.COMMANDS_TTM)

        for i in range(0, 12):
            self._update_shm(data, f'{config.SHM.TTM}{i:02d}')

        return data

    @emit
    @timeit
    def focusing_sequence_fits(self) -> dict[str, Any]:
        data = {}

        self._update_fits_full(data, config.FITS.last_focus_sequence)

        return data

    @emit
    @timeit
    def calibration_sequence(self) -> dict[str, Any]:
        data = {}

        self._update_dict(
            data, 'memory', {
                'calibration_poses': {
                    'list': memory.hget('calibration_poses', 'list')
                }
            })

        return data

    @emit
    @timeit
    def centering_spiral_data(self) -> dict[str, Any]:
        data = {}

        self._update_dict(
            data, 'memory', {
                'spiral_search':
                    memory.hmget(
                        'spiral_search', {
                            'radius': int,
                            'overlap': float,
                            'expno': int,
                            'star_x': float,
                            'star_y': float
                        })
            })

        return data

    def sequencer_abort(self) -> None:
        requests.post(
            f'http://{config.Sequencer.host}:{config.Sequencer.port}/abort')

    def plots_data_db(self, *, since: datetime, until: datetime,
                      monitoring_keys: list[str],
                      obs_keys: list[str]) -> dict[str, Any]:
        data = {}

        if len(monitoring_keys) > 0:
            data['monitoring'] = database.read_mongo_to_pandas(
                'monitoring', keys=monitoring_keys, since=since, until=until)

        if len(obs_keys) > 0:
            data['obs'] = database.read_mongo_to_pandas(
                'obs', keys=obs_keys, since=since, until=until)

        return data

    def plots_data_live(self) -> dict[str, Any]:
        data = monitoring.gather_general() | monitoring.gather_ao()
        data['timestamp'] = datetime.now(timezone.utc)

        return data

    def ao_calibration_ready(self, *, conf: str, loop: int) -> dict[str, Any]:
        if not wfs.acquisition_running():
            return {'ready': False, 'reason': 'WFS acquisition is not running'}

        if not wfs.check_flux():
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

    def ao_calibration_data(self, *, conf: str, loop: int) -> dict[str, Any]:
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

    def ao_calibration_reload(self, *, conf: str, loop: int) -> dict[str, Any]:
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/apply-calib-saved.sh'

        res = subprocess.run([script], timeout=60, capture_output=True,
                             cwd=config.AO.cacao_workdir)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode(errors='replace')

        return data

    def ao_calibration_prepare(self, *, conf: str,
                               loop: int) -> dict[str, Any]:
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

    def ao_calibration_mlat(self, *, conf: str, loop: int) -> dict[str, Any]:
        data = {}

        ready_data = self.ao_calibration_ready(conf=conf, loop=loop)
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
        data['stdout'] = res.stdout.decode(errors='replace')

        if res.returncode != 0:
            return data

        self._update_fps_param(data, f'mlat-{loop}', 'out.framerateHz')
        self._update_fps_param(data, f'mlat-{loop}', 'out.latencyfr')

        data['hardwlatencypts'] = np.loadtxt(
            config.AO.cacao_workdir /
            f'KalAO-{conf}-rootdir/rundir/fps.mlat-{loop}.datadir/hardwlatencypts.dat'
        )

        return data

    def ao_calibration_mkDMpokemodes(self, *, conf: str,
                                     loop: int) -> dict[str, Any]:
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/01-mkDMpokemodes.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode(errors='replace')

        return data

    def ao_calibration_takeref(self, *, conf: str,
                               loop: int) -> dict[str, Any]:
        data = {}

        ready_data = self.ao_calibration_ready(conf=conf, loop=loop)
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
        data['stdout'] = res.stdout.decode(errors='replace')

        return data

    def ao_calibration_acqlinResp(self, *, conf: str,
                                  loop: int) -> dict[str, Any]:
        data = {}

        ready_data = self.ao_calibration_ready(conf=conf, loop=loop)
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
        data['stdout'] = res.stdout.decode(errors='replace')

        return data

    def ao_calibration_RMHdecode(self, *, conf: str,
                                 loop: int) -> dict[str, Any]:
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/04-RMHdecode.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode(errors='replace')

        self._update_fits(
            data, config.AO.cacao_workdir /
            f'KalAO-{conf}-rootdir/conf/RMmodesWFS/zrespM-H.fits')

        return data

    def ao_calibration_RMmkmask(self, *, conf: str,
                                loop: int) -> dict[str, Any]:
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/05-RMmkmask.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode(errors='replace')

        return data

    def ao_calibration_compCM(self, *, conf: str, loop: int) -> dict[str, Any]:
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/06-compCM.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode(errors='replace')

        return data

    def ao_calibration_load(self, *, conf: str, loop: int) -> dict[str, Any]:
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/apply-calib-rootdir.sh'

        res = subprocess.run([script], timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode(errors='replace')

        return data

    def ao_calibration_save(self, *, conf: str, loop: int,
                            comment: str) -> dict[str, Any]:
        data = {}

        script = config.AO.cacao_workdir / f'scripts/{conf}/save-calib.sh'

        if comment != '':
            args = [script, comment]
        else:
            args = [script]

        res = subprocess.run(args, timeout=60, capture_output=True)

        data['returncode'] = res.returncode
        data['stdout'] = res.stdout.decode(errors='replace')

        return data

    ##### Science Camera

    def centering_manual_offsets(self, *, dx: float, dy: float) -> None:
        centering.manual_centering(dx, dy)

    def centering_manual_validate(self) -> None:
        centering.validate_manual_centering()

    ##### Loop controls

    # DM Loop

    def ao_dmloop_on(self, *, state: bool) -> None:
        aocontrol.switch_loop(config.AO.DM_loop_number, state,
                              with_autogain=False, autozero=False)

    def ao_dmloop_gain(self, *, gain: float) -> None:
        aocontrol.set_dmloop_gain(gain)

    def ao_dmloop_mult(self, *, mult: float) -> None:
        aocontrol.set_dmloop_mult(mult)

    def ao_dmloop_limit(self, *, limit: float) -> None:
        aocontrol.set_dmloop_limit(limit)

    def ao_dmloop_zero(self) -> None:
        aocontrol.dmloop_zero()

    # TTM Loop

    def ao_ttmloop_on(self, *, state: bool) -> None:
        aocontrol.switch_loop(config.AO.TTM_loop_number, state,
                              with_autogain=False, autozero=False)

    def ao_ttmloop_gain(self, *, gain: float) -> None:
        aocontrol.set_ttmloop_gain(gain)

    def ao_ttmloop_mult(self, *, mult: float) -> None:
        aocontrol.set_ttmloop_mult(mult)

    def ao_ttmloop_limit(self, *, limit: float) -> None:
        aocontrol.set_ttmloop_limit(limit)

    def ao_ttmloop_zero(self) -> None:
        aocontrol.ttmloop_zero()

    # Wavefront Sensor

    def wfs_emgain(self, *, emgain: int) -> None:
        wfs.set_emgain(emgain)

    def wfs_exposuretime(self, *, exposuretime: float) -> None:
        wfs.set_exptime(exposuretime)

    def wfs_autogain_on(self, *, state: bool) -> None:
        aocontrol.switch_autogain(state)

    def wfs_autogain_setting(self, *, setting: int) -> None:
        wfs.set_autogain_setting(setting)

    # Deformable Mirror

    def dm_maxstroke(self, *, stroke: float) -> None:
        aocontrol.set_dm_max_stroke(stroke)

    def dm_strokemode(self, *, mode: int) -> None:
        aocontrol.set_dm_stroke_mode(mode)

    def dm_targetstroke(self, *, target: float) -> None:
        aocontrol.set_dm_target_stroke(target)

    # Observation

    def adc_synchronisation(self, *, state: bool) -> None:
        adc.set_synchronisation(state)

    def ttm_offloading(self, *, state: bool) -> None:
        ttm.set_offloading(state)

    # Modal gains

    def ao_dmloop_modalgains(self, *, modalgains: list) -> None:
        aocontrol.set_modalgains(modalgains)

    ##### Engineering

    # PLC / Misc. hardware

    def hardware_shutter_status(self, *, status: str) -> None:
        shutter._switch(ShutterStatus(status))

    def hardware_shutter_init(self) -> None:
        shutter.init()

    def hardware_flipmirror_status(self, *, status: str) -> None:
        flipmirror._switch(FlipMirrorStatus(status))

    def hardware_flipmirror_init(self) -> None:
        flipmirror.init()

    def hardware_calibunit_position(self, *, position: float) -> None:
        calibunit.move(position)

    def hardware_calibunit_init(self) -> None:
        calibunit.init(force_init=True)

    def hardware_calibunit_stop(self) -> None:
        calibunit.stop()

    def hardware_calibunit_laser(self) -> None:
        calibunit.move_to_laser_position()

    def hardware_calibunit_tungsten(self) -> None:
        calibunit.move_to_tungsten_position()

    def hardware_tungsten_status(self, *, status: bool) -> None:
        if status:
            tungsten.on()
        else:
            tungsten.off()

    def hardware_tungsten_init(self) -> None:
        tungsten.init()

    def hardware_laser_status(self, *, status: bool) -> None:
        if status:
            laser.enable()
        else:
            laser.disable()

    def hardware_laser_power(self, *, power: float) -> None:
        laser.set_power(power)

    def hardware_laser_init(self) -> None:
        laser.init()

    def hardware_lamps_off(self) -> None:
        hw_utils.lamps_off()

    def hardware_filterwheel_filter(self, *, filter: str) -> None:
        filterwheel.set_filter(filter)

    def hardware_filterwheel_init(self) -> None:
        filterwheel.init()

    def hardware_adc1_angle(self, *, position: float) -> None:
        adc.rotate(config.PLC.Node.ADC1, position)

    def hardware_adc1_init(self) -> None:
        adc.init(config.PLC.Node.ADC1, force_init=True)

    def hardware_adc1_stop(self) -> None:
        adc.stop(config.PLC.Node.ADC1)

    def hardware_adc2_angle(self, *, position: float) -> None:
        adc.rotate(config.PLC.Node.ADC2, position)

    def hardware_adc2_init(self) -> None:
        adc.init(config.PLC.Node.ADC2, force_init=True)

    def hardware_adc2_stop(self) -> None:
        adc.stop(config.PLC.Node.ADC2)

    def hardware_adc_zerodisp(self) -> None:
        adc.set_zero_disp()

    def hardware_adc_maxdisp(self) -> None:
        adc.set_max_disp()

    def hardware_adc_angleoffset(self, *, angle: float, offset: float) -> None:
        adc.set_angle(angle, offset)

    def hardware_pump_status(self, *, status: bool) -> None:
        if status:
            cooling.pump_on()
        else:
            cooling.pump_off()

    def hardware_fan_status(self, *, status: bool) -> None:
        if status:
            cooling.heatexchanger_fan_on()
        else:
            cooling.heatexchanger_fan_off()

    def hardware_heater_status(self, *, status: bool) -> None:
        if status:
            cooling.heater_on()
        else:
            cooling.heater_off()

    # Camera

    def camera_exptime(self, *, exposure_time: float) -> None:
        camera.set_exposure_time(exposure_time)

    def camera_take(self, *, exposure_time: float, frames: int,
                    roi_size: int) -> None:
        template = Template(id=TemplateID.ENGINEERING,
                            start=datetime.now(timezone.utc), nexp=1)

        camera.take_science_image(template, exptime=exposure_time,
                                  nbframes=frames, roi_size=roi_size)

    def camera_cancel(self) -> None:
        camera.cancel()

    # Wavefront Sensor

    def wfs_acquisition_start(self) -> None:
        wfs.start_acquisition()

    def wfs_acquisition_stop(self) -> None:
        wfs.stop_acquisition()

    # Deformable Mirror

    def dm_on(self) -> None:
        dm.on()

    def dm_off(self) -> None:
        dm.off()

    # IPPower

    def ippower_rtc_on(self) -> None:
        ippower.switch(config.IPPower.Port.RTC, IPPowerStatus.ON)

    def ippower_rtc_off(self) -> None:
        ippower.switch(config.IPPower.Port.RTC, IPPowerStatus.OFF)

    def ippower_bench_on(self) -> None:
        ippower.switch(config.IPPower.Port.Bench, IPPowerStatus.ON)

    def ippower_bench_off(self) -> None:
        ippower.switch(config.IPPower.Port.Bench, IPPowerStatus.OFF)

    def ippower_dm_on(self) -> None:
        ippower.switch(config.IPPower.Port.DM, IPPowerStatus.ON)

    def ippower_dm_off(self) -> None:
        ippower.switch(config.IPPower.Port.DM, IPPowerStatus.OFF)

    def services_action(self, *, unit: str, action: str) -> None:
        services.unit_control(unit, ServiceAction(action))

    # DM channels

    def channels_resetall(self, *, dm_number: int) -> None:
        aocontrol.reset_dm(dm_number)

    def channels_reset(self, *, dm_number: int, channel: int) -> None:
        aocontrol.reset_channel(dm_number, channel)

    # DM & TTM control

    def dm_pattern(self, *, pattern: np.ndarray) -> None:
        dm.set_pattern(config.SHM.DM_USER_CONTROLLED, pattern)

    def ttm_position(self, *, tip: float, tilt: float) -> None:
        ttm.set_tiptilt(config.SHM.TTM_USER_CONTROLLED, tip, tilt)

    # Centering

    def centering_star(self) -> None:
        centering.center_on_target()

    def centering_laser(self) -> None:
        centering.center_on_laser()

    def centering_spiral(self) -> None:
        centering.spiral_search()

    # Focusing

    def focusing_autofocus(self) -> None:
        focusing.autofocus()

    def focusing_sequence(self) -> None:
        template = Template(id=TemplateID.FOCUS,
                            start=datetime.now(timezone.utc),
                            nexp=config.Focusing.nexp)

        focusing.focus_sequence(template)

    # Dead-man

    def deadman(self, *, count: int) -> None:
        database.store('obs', {'deadman_keepalive': count})

    # Instrument / RTC

    def instrument_shutdown(self) -> None:
        return rtc.shutdown_sequence()

    def rtc_poweroff(self) -> None:
        return rtc.power_off()

    def rtc_reboot(self) -> None:
        return rtc.reboot()

    ##### Logs

    def logs(self, *, timestamp: datetime = None, cursor: str = None,
             lines: int = None) -> list[LogEntry]:
        if timestamp is not None:
            return logs.get_entries_since_timestamp(timestamp)
        elif cursor is not None:
            return logs.get_entries_since_cursor(cursor)
        elif lines is not None:
            return logs.get_entires_by_lines(lines)

    def logs_between(self, *, since: datetime,
                     until: datetime) -> list[LogEntry]:
        return logs.get_entries_between(since, until)
