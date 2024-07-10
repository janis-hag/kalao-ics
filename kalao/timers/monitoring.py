#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : monitoring.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
monitoring.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""
import math
import signal
import threading
from datetime import datetime, timezone
from types import FrameType
from typing import Any, Callable

import numpy as np

from kalao import database, euler, ippower, logger
from kalao.cacao import aocontrol, toolbox
from kalao.hardware import camera, hw_utils
from kalao.rtc import gpu, sensors
from kalao.utils import kstring

import schedule

from kalao.definitions.enums import CameraServerStatus, LoopStatus

import config

ao_job: schedule.Job | None = None
sleeper = threading.Event()


def _update_ao_job(ao_on: bool | None = None) -> None:
    global ao_job

    if ao_on is None:
        ao_on = aocontrol.check_loops() != LoopStatus.ALL_LOOPS_OFF

    if ao_on and ao_job is None:
        logger.info('monitoring_timer', 'Switching to fast monitoring for AO')
        ao_job = schedule.every(config.Monitoring.ao_update_interval
                                ).seconds.do(run_threaded, _update_ao)
        sleeper.set()

    elif not ao_on and ao_job is not None:
        logger.info('monitoring_timer', 'Switching to slow monitoring for AO')
        schedule.cancel_job(ao_job)
        ao_job = None
        sleeper.set()


def gather_general() -> dict[str, Any]:
    data = {}

    # Get monitoring from plc and store
    hw_values = hw_utils.get_all_status()
    data.update(hw_values)

    # Get RTC data
    rtc_sensors = sensors.status()
    data.update(rtc_sensors)

    rtc_gpu = gpu.status()
    data.update(rtc_gpu)

    # IPPower
    ippower_status = ippower.status_all()
    data.update(ippower_status)

    # Science camera status
    camera_server_status = camera.server_status()
    data.update({'camera_server_status': camera_server_status})

    if camera_server_status == CameraServerStatus.UP:
        camera_data = {}

        camera_data['camera_status'] = camera.get_camera_status()

        camera_temperatures = camera.get_temperatures()
        camera_data['camera_ccd_temp'] = camera_temperatures['ccd']
        camera_data['camera_heatsink_temp'] = camera_temperatures['heatsink']

        data.update(camera_data)

    # Telescope
    telescope = euler.telescope_coord_altaz()
    telescope_status = {
        'telescope_altitude': telescope.alt.deg,
        'telescope_azimut': telescope.az.deg
    }
    data.update(telescope_status)

    # KalAO dynamic config

    config_fps = toolbox.open_fps_once(config.FPS.CONFIG)
    if config_fps is not None:
        data['ttm_offloading'] = config_fps.get_param('ttm_offloading')
        data['adc_synchronisation'] = config_fps.get_param(
            'adc_synchronisation')

    # Nuvu (camstack) stream
    nuvu_raw_shm = toolbox.open_shm_once(config.SHM.NUVU_RAW)

    if nuvu_raw_shm is not None:
        stream_keywords = nuvu_raw_shm.get_keywords()

        data['wfs_ccd_temp'] = stream_keywords.get('T_CCD', np.nan)
        data['wfs_controller_temp'] = stream_keywords.get('T_CNTRLR', np.nan)
        data['wfs_powersupply_temp'] = stream_keywords.get('T_PSU', np.nan)
        data['wfs_fpga_temp'] = stream_keywords.get('T_FPGA', np.nan)
        data['wfs_heatsink_temp'] = stream_keywords.get('T_HSINK', np.nan)

    return data


def gather_ao() -> dict[str, Any]:
    data = {}

    # Nuvu (camstack) stream
    nuvu_raw_shm = toolbox.open_shm_once(config.SHM.NUVU_RAW)

    if nuvu_raw_shm is not None:
        stream_keywords = nuvu_raw_shm.get_keywords()

        maqtime = datetime.fromtimestamp(stream_keywords['_MAQTIME'] / 1e6,
                                         tz=timezone.utc)
        acquisition_running = (
            datetime.now(timezone.utc) -
            maqtime).total_seconds() < config.WFS.acquisition_time_timeout

        data['wfs_emgain'] = stream_keywords.get('EMGAIN', np.nan)
        data['wfs_detgain'] = stream_keywords.get('DETGAIN', np.nan)
        data['wfs_exposuretime'] = stream_keywords.get('EXPTIME', np.nan)
        data['wfs_acquisition_running'] = acquisition_running
        data['wfs_framerate'] = stream_keywords.get('MFRATE', np.nan)

    # Nuvu process
    nuvu_fps = toolbox.open_fps_once(config.FPS.NUVU)

    if nuvu_fps is not None and nuvu_fps.run_isrunning():
        data['wfs_autogain_on'] = nuvu_fps.get_param('autogain_on')
        data['wfs_autogain_setting'] = nuvu_fps.get_param('autogain_setting')

    # BMC process
    bmc_fps = toolbox.open_fps_once(config.FPS.BMC)

    if bmc_fps is not None and bmc_fps.run_isrunning():
        data['dm_max_stroke'] = bmc_fps.get_param('max_stroke')
        data['dm_stroke_mode'] = bmc_fps.get_param('stroke_mode')
        data['dm_target_stroke'] = bmc_fps.get_param('target_stroke')

    # SHWFS process
    shwfs_fps = toolbox.open_fps_once(config.FPS.SHWFS)

    if shwfs_fps is not None and shwfs_fps.run_isrunning():
        data['wfs_algorithm'] = shwfs_fps.get_param('algorithm')
        data['wfs_flux_avg'] = shwfs_fps.get_param('flux_avg')
        data['wfs_flux_max'] = shwfs_fps.get_param('flux_max')
        data['wfs_residual_rms'] = shwfs_fps.get_param('residual_rms')
        data['wfs_slope_x_avg'] = shwfs_fps.get_param('slope_x_avg')
        data['wfs_slope_y_avg'] = shwfs_fps.get_param('slope_y_avg')

    # Tip/tilt stream
    ttm_shm = toolbox.open_shm_once(config.SHM.TTM)

    if ttm_shm is not None:
        # Check turned off to prevent timeout. Data may be obsolete
        tt_data = ttm_shm.get_data(check=False)

        data['ttm_tip'] = float(tt_data[0])
        data['ttm_tilt'] = float(tt_data[1])

    # DM loop process
    dmloop_fps = toolbox.open_fps_once(config.FPS.DMLOOP)

    if dmloop_fps is not None and dmloop_fps.run_isrunning():
        data['dmloop_on'] = dmloop_fps.get_param('loopON')
        data['dmloop_gain'] = dmloop_fps.get_param('loopgain')
        data['dmloop_mult'] = dmloop_fps.get_param('loopmult')
        data['dmloop_limit'] = dmloop_fps.get_param('looplimit')

    # TTM loop process
    ttmloop_fps = toolbox.open_fps_once(config.FPS.TTMLOOP)

    if ttmloop_fps is not None and ttmloop_fps.run_isrunning():
        data['ttmloop_on'] = ttmloop_fps.get_param('loopON')
        data['ttmloop_gain'] = ttmloop_fps.get_param('loopgain')
        data['ttmloop_mult'] = ttmloop_fps.get_param('loopmult')
        data['ttmloop_limit'] = ttmloop_fps.get_param('looplimit')

    return data


def check_warning_error(key: str, value: Any) -> [str, str, Any]:
    metadata = database.definitions['monitoring']['metadata'][key]

    error_values = metadata.get('error_values', [])
    is_numeric = isinstance(value, float) or isinstance(value, int)

    if value in error_values or (is_numeric and np.isnan(value) and
                                 np.isnan(error_values).any()):
        return 'error', '==', value
    elif is_numeric:
        error_range = metadata.get('error_range', [np.nan, np.nan])
        warn_range = metadata.get('warn_range', [np.nan, np.nan])

        error_min = error_range[0]
        error_max = error_range[1]
        warn_min = warn_range[0]
        warn_max = warn_range[1]

        if value > error_max:
            return 'error', '>', error_max
        elif value < error_min:
            return 'error', '<', error_min
        elif value > warn_max:
            return 'warning', '>', warn_max
        elif value < warn_min:
            return 'warning', '<', warn_min
        else:
            return '', '', None
    else:
        return '', '', None


def _update_general() -> None:
    data = gather_general()

    if ao_job is None:
        data |= gather_ao()

    timestamp = datetime.now(timezone.utc)

    for key in data.keys():
        data[key] = _round(key, data[key])
        _check_and_log(key, data[key], timestamp)

    if data != {}:
        database.store('monitoring', data, timestamp=timestamp)

    if ao_job is None:
        _update_ao_job(
            data.get('dmloop_on', False) or data.get('ttmloop_on', False))


def _update_ao() -> None:
    data = gather_ao()
    timestamp = datetime.now(timezone.utc)

    for key in data.keys():
        data[key] = _round(key, data[key])
        _check_and_log(key, data[key], timestamp)

    if data != {}:
        database.store('monitoring', data, timestamp=timestamp)

    _update_ao_job(
        data.get('dmloop_on', False) or data.get('ttmloop_on', False))


def _round(key: str, value: Any):
    metadata = database.definitions['monitoring']['metadata'][key]

    rounding = metadata.get('rounding')

    if rounding is None:
        return value
    elif np.isnan(value):
        return value
    elif rounding == 0:
        return round(value)
    else:
        return round(value, rounding)


def _check_and_log(key: str, value: Any, timestamp: datetime) -> None:
    metadata = database.definitions['monitoring']['metadata'][key]

    level, condition, threshold = check_warning_error(key, value)

    if level != '':
        unit = kstring.get_unit_string(metadata)

        if level == 'error':
            log_func = logger.error
        elif level == 'warning':
            log_func = logger.warn

        if condition == '>':
            verb = 'over'
        elif condition == '<':
            verb = 'under'

        data = database.get_time_since_state('monitoring', key, condition,
                                             threshold)

        if data.get('since') is None:
            since = 0  # s
        else:
            since = (timestamp - data['since']['timestamp']).total_seconds()

            last = (data['current']['timestamp'] -
                    data['since']['timestamp']).total_seconds()

            if last // config.Monitoring.warning_repetition_rate == since // config.Monitoring.warning_repetition_rate:
                return

        hr, min, sec = _sec_to_hms(since)

        since_str = f'{sec:.0f}s'

        if min != 0 or hr != 0:
            since_str = f'{min:d}m ' + since_str

        if hr != 0:
            since_str = f'{hr:d}h ' + since_str

        if condition == '==':
            log_func('monitoring_timer',
                     f'{key} = {value}{unit} (since {since_str})')
        else:
            log_func(
                'monitoring_timer',
                f'{key} = {value}{unit} {verb} {level} threshold of {threshold}{unit} (since {since_str})'
            )


def _sec_to_hms(sec: float, decimal: int = 0) -> tuple[int, int, float | int]:
    if decimal == 0:
        sec = round(sec)
    else:
        sec = round(sec, decimal)

    hr = math.floor(sec / 3600)
    min = math.floor((sec/60) % 60)
    sec = sec % 60

    return hr, min, sec


if __name__ == '__main__':

    def run_threaded(job_func: Callable) -> None:
        job_thread = threading.Thread(target=job_func)
        job_thread.start()

    def sighup_handler(signal_received: int, frame: FrameType | None) -> None:
        _update_ao_job()

    signal.signal(signal.SIGHUP, sighup_handler)

    schedule.every(config.Monitoring.update_interval).seconds.do(
        run_threaded, _update_general)
    _update_ao_job()

    while True:
        n = schedule.idle_seconds()

        if n is None:
            break
        elif n > 0:
            sleeper.wait(n)

        if sleeper.is_set():
            sleeper.clear()

        schedule.run_pending()
