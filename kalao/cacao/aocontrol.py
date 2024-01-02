#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : com_tools.py
# @Date : 2022-06-13-09-51
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
aocontrol.py is part of the KalAO Instrument Control Software (KalAO-ICS).
"""

import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from kalao import ippower, logger
from kalao.cacao import toolbox
from kalao.utils import kalao_tools

import libtmux
import libtmux.exc

from tcs_communication import t120

from kalao.definitions.enums import IPPowerStatus, LoopStatus, ReturnCode

import config

shm_and_fps_cache = {}


def close_loops():
    """
    Close the primary DM AO loop followed by the secondary TTM loop.

    :return:
    """

    return switch_loops(close=True)


def open_loops():
    """
    Open the primary DM AO loop followed by the secondary TTM loop.

    :return:
    """

    return switch_loops(close=False)


def check_loops():
    status = LoopStatus(0)

    dmloop_fps = toolbox.open_fps_once(config.FPS.DMLOOP, shm_and_fps_cache)

    if dmloop_fps is not None and dmloop_fps.get_param('loopON'):
        status |= LoopStatus.DM_LOOP_ON

    ttmloop_fps = toolbox.open_fps_once(config.FPS.TTMLOOP, shm_and_fps_cache)

    if ttmloop_fps is not None and ttmloop_fps.get_param('loopON'):
        status |= LoopStatus.TTM_LOOP_ON

    return status


def switch_loops(close=True):
    """
    Toggle the loop value of the primary DM AO loop and the secondary TTM loop.

    :return:
    """

    if close:
        logger.info('ao', 'Closing both loops')
        loop_order = [config.AO.DM_loop_number, config.AO.TTM_loop_number]
    else:
        logger.info('ao', 'Opening both loops')
        loop_order = [config.AO.TTM_loop_number, config.AO.DM_loop_number]

    for i in loop_order:
        switch_loop(i, close)

    return check_loops()


def close_loop(loop_number):
    return switch_loop(loop_number, close=True)


def open_loop(loop_number):
    return switch_loop(loop_number, close=False)


def switch_loop(loop_number, close=True):
    """
    Toggle the loop value of one loop

    :return:
    """

    if close:
        logger.info('ao', f'Closing loop {loop_number}')
    else:
        logger.info('ao', f'Opening loop {loop_number}')

    fps_mfilt = toolbox.open_fps_once(f'mfilt-{loop_number}',
                                      shm_and_fps_cache)

    if fps_mfilt is None:
        logger.error('ao', f'mfilt-{loop_number} is missing')

        return LoopStatus.ERROR

    fps_mfilt.set_param('loopON', close)

    if not close:
        fps_mfilt.set_param('loopZERO', True)

    time.sleep(1)

    if loop_number == 1:
        ret = switch_autogain(on=close)

        if ret != 0:
            return ret  #TODO

    return check_loops()


def autogain_on():
    return switch_autogain(on=True)


def autogain_off():
    return switch_autogain(on=False)


def switch_autogain(on=True):
    return _set_fps_value(config.FPS.NUVU, 'autogain_on', on)


def set_autogain_setting(setting):
    setting = int(setting)

    if setting > config.WFS.max_autogain_setting:
        setting = config.WFS.max_autogain_setting
    elif setting < 0:
        setting = 0

    return _set_fps_value(config.FPS.NUVU, 'autogain_setting', setting)


def set_emgain(emgain=1, method='fps'):
    """
    Set the EM gain of the Nuvu WFS camera.

    :param emgain: EM gain to set. 1 by default for no gain.
    :return:
    """

    emgain = int(emgain)

    if emgain < config.WFS.min_emgain:
        emgain = config.WFS.min_emgain
    elif emgain > config.WFS.max_emgain:
        emgain = config.WFS.max_emgain

    if method == 'fps':
        _set_fps_value(config.FPS.NUVU, 'emgain', emgain)
    elif method == 'tmux':
        _set_tmux_value('nuvu_ctrl', 'SetEMCalibratedGain', emgain)
    else:
        logger.error('ao', f'Unknown method {method} in set_emgain')

    return 0


def set_exptime(exptime=0, method='fps'):
    """
    Set the exposure time of the Nuvu WFS camera.

    :param exptime: exposure time to set in milliseconds. 0 by default for highest frame rate.
    :return:
    """

    if exptime < config.WFS.min_exposuretime:
        exptime = config.WFS.min_exposuretime
    elif exptime > config.WFS.max_exposuretime:
        exptime = config.WFS.max_exposuretime

    if method == 'fps':
        _set_fps_value(config.FPS.NUVU, 'exposuretime', exptime)
    elif method == 'tmux':
        _set_tmux_value('nuvu_ctrl', 'SetExposureTime', exptime)
    else:
        logger.error('ao', f'Unknown method {method} in set_exptime')

    return 0


def emgain_off():
    """
    Completely turn of EM gain on the WFS camera. For double safety the command is sent directly to the tmux as well as
    to the nuvu_acquire fps.

    :return: 0 on success
    """

    ret = 0

    try:
        _set_fps_value(config.FPS.NUVU, 'autogain_on', False)
        _set_fps_value(config.FPS.NUVU, 'autogain_setting', 0)
    except Exception as err:
        print(
            f'Can\'t turn off autogain, {config.FPS.NUVU} seems not to be running.'
        )
        print(Exception, err)
        ret = -1

    try:
        _set_fps_value(config.FPS.NUVU, 'emgain', 1)
    except Exception as err:
        print(
            f'Can\'t turn off emgain, {config.FPS.NUVU} seems not to be running.'
        )
        print(Exception, err)
        ret = -1

    try:
        _set_tmux_value('nuvu_ctrl', 'SetEMCalibratedGain', 1)
    except Exception as err:
        print(f'Can\'t turn off emgain, nucu_ctrl seems not to be running.')
        print(Exception, err)
        ret = -1

    return ret


def set_dmloop_gain(gain):
    return _set_fps_value(config.FPS.DMLOOP, 'loopgain', gain)


def set_dmloop_mult(mult):
    return _set_fps_value(config.FPS.DMLOOP, 'loopmult', mult)


def set_dmloop_limit(limit):
    return _set_fps_value(config.FPS.DMLOOP, 'looplimit', limit)


def set_ttmloop_gain(gain):
    return _set_fps_value(config.FPS.TTMLOOP, 'loopgain', gain)


def set_ttmloop_mult(mult):
    return _set_fps_value(config.FPS.TTMLOOP, 'loopmult', mult)


def set_ttmloop_limit(limit):
    return _set_fps_value(config.FPS.TTMLOOP, 'looplimit', limit)


def set_modalgains(modalgains, stream_name=config.Streams.MODALGAINS):
    modalgains_stream = toolbox.open_stream_once(stream_name,
                                                 shm_and_fps_cache)

    delta = modalgains_stream.size - modalgains.size

    if modalgains_stream is not None:
        if delta < 0:
            modalgains_stream.set_data(modalgains[:delta], True)
        elif delta > 0:
            modalgains_stream.set_data(
                np.pad(modalgains, (0, delta), constant_values=0), True)
        else:
            modalgains_stream.set_data(modalgains, True)

        return 0

    else:
        return -1


def set_bmc_max_stroke(max_stroke):
    return _set_fps_value(config.FPS.BMC, 'max_stroke', max_stroke)


def set_bmc_stroke_mode(stroke_mode):
    return _set_fps_value(config.FPS.BMC, 'stroke_mode', stroke_mode)


def tip_tilt_offload_ttm_to_telescope(gain=config.TTM.offload_gain,
                                      override_threshold=False,
                                      input_stream=config.Streams.TTM,
                                      port=config.T120.port):
    """
    Offload current tip/tilt on the telescope by sending corresponding alt/az offsets.
    The gain can be adjusted to set how much of the tip/tilt should be offloaded.

    :param gain: Gain factor, set to 0.25 by default.
    :return:
    """

    ttm_stream = toolbox.open_stream_once(input_stream, shm_and_fps_cache)

    if ttm_stream is None:
        logger.error('ttm', f'{input_stream} is missing')
        return -1

    tip, tilt = ttm_stream.get_data(check=False)

    to_offload = np.sqrt(tip**2 + tilt**2)

    if override_threshold or to_offload > config.TTM.offload_threshold:
        alt_offload = tip * config.TTM.tip_to_onsky * gain
        az_offload = tilt * config.TTM.tilt_to_onsky * gain

        # Keep offsets within defined range
        alt_offload = np.clip(alt_offload, -config.TTM.max_tel_offload,
                              config.TTM.max_tel_offload)
        az_offload = np.clip(az_offload, -config.TTM.max_tel_offload,
                             config.TTM.max_tel_offload)

        logger.info(
            'ttm',
            f'Offloading tip-tilt to telescope. On TTM: tip={tip}mrad, tilt={tilt}mrad. Offloaded: alt={alt_offload}asec, az={az_offload}asec'
        )

        t120.send_altaz_offset(alt_offload, az_offload, port=port)

    return 0


def tip_tilt_offset_fli_to_ttm(x_tip, y_tilt, absolute=False,
                               output_stream=config.Streams.TTM_CENTERING):
    """
    Moves the tip tilt mirror by sending an offset in mrad. The value as input is given in pixels and converted.

    :param x_tip: number of pixels to tip
    :param y_tilt: number of pixels to tilt
    :param absolute: Flag to indicate that tip tilt values are in absolute radian. By default, set to False.
    :param output_stream: name of the stream to use to set the offset.

    :return:
    """

    ttm_stream = toolbox.open_stream_once(output_stream, shm_and_fps_cache)

    if ttm_stream is None:
        logger.error('ttm', f'{output_stream} is missing')
        return -1

    tip, tilt = ttm_stream.get_data(check=False)

    # TIP
    if absolute:
        new_tip = x_tip
    else:
        new_tip = tip + x_tip * config.AO.FLI_tip_to_TTM

    # TILT
    if absolute:
        new_tilt = y_tilt
    else:
        new_tilt = tilt + y_tilt * config.AO.FLI_tilt_to_TTM

    new_tip, new_tilt = check_ttm_saturation(new_tip, new_tilt)

    logger.info(
        'ttm',
        f'Changing tip-tilt based on FLI. On FLI: tip={x_tip}px, tilt={y_tilt}px. TTM set to: tip={new_tip}mrad, tilt={new_tilt}mrad'
    )

    ttm_stream.set_data(np.array([new_tip, new_tilt]), True)

    return 0


def tip_tilt_wfs_to_ttm(tt_threshold=config.WFS.centering_slope_threshold,
                        output_stream=config.Streams.TTM_CENTERING):
    """
    Precise tip/tilt centering on the wavefront sensor.

    :param tt_threshold: precision at which the centering need to be based on the residual slope.
    :return:
    """

    tip_centered = False
    tilt_centered = False

    ttm_stream = toolbox.open_stream_once(output_stream, shm_and_fps_cache)
    slopes_fps = toolbox.open_fps_once(config.FPS.SHWFS, shm_and_fps_cache)

    if ttm_stream is None:
        logger.error('ttm', f'{output_stream} is missing')
        return -1

    if slopes_fps is None:
        logger.error('ttm', f'{config.FPS.SHWFS} is missing')
        return -1

    # TODO verify that shwfs enough illuminated for centering

    timeout_time = time.monotonic() + config.Starfinder.centering_timeout

    while not (tip_centered and tilt_centered):
        if time.monotonic() > timeout_time:
            logger.error('ttm', f'Timeout during centering using WFS')
            return -1

        tip, tilt = ttm_stream.get_data(check=False)

        tip_residual = slopes_fps.get_param('slope_y')
        tilt_residual = slopes_fps.get_param('slope_x')

        if np.abs(tip_residual) < tt_threshold:
            tip_centered = True
            new_tip = tip
        else:
            new_tip = tip + tip_residual * config.AO.WFS_tip_to_TTM

        if np.abs(tilt_residual) < tt_threshold:
            tilt_centered = True
            new_tilt = tilt
        else:
            new_tilt = tilt + tilt_residual * config.AO.WFS_tilt_to_TTM

        new_tip, new_tilt = check_ttm_saturation(new_tip, new_tilt)

        logger.info(
            'ttm',
            f'Changing tip-tilt based on WFS. On WFS: tip={tip_residual}px, tilt={tilt_residual}px. TTM set to: tip={new_tip}mrad, tilt={new_tilt}mrad'
        )

        ttm_stream.set_data(np.array([new_tip, new_tilt]), True)

        time.sleep(1)

    return 0


def check_ttm_saturation(tip, tilt):
    if tip > 2.45:
        logger.warn('ttm', 'TTM saturated, limiting tip to 2.45')
        tip = 2.45
    elif tip < -2.45:
        logger.warn('ttm', 'TTM saturated, limiting tip to -2.45')
        tip = -2.45

    if tilt > 2.45:
        logger.warn('ttm', 'TTM saturated, limiting tilt to 2.45')
        tilt = 2.45
    elif tilt < -2.45:
        logger.warn('ttm', 'TTM saturated, limiting tilt to -2.45')
        tilt = -2.45

    return tip, tilt


def optimize_wfs_flux():
    nuvu_acquire_fps = toolbox.open_fps_once(config.FPS.NUVU,
                                             shm_and_fps_cache)

    if nuvu_acquire_fps is None:
        logger.error('nuvu', f'{config.FPS.NUVU} is missing')
        return -1

    # Check if we are already good
    if check_wfs_flux():
        return 0

    nuvu_acquire_fps.set_param('autogain_setting', 0)

    for setting in range(config.WFS.max_autogain_setting + 1):
        nuvu_acquire_fps.set_param('autogain_setting', setting)

        time.sleep(nuvu_acquire_fps.get_param('autogain_wait') / 1000)

        for i in range(10):
            if check_wfs_flux():
                return 0

    # Reset values if no signal detected
    nuvu_acquire_fps.set_param('autogain_setting', 0)
    set_emgain(1)
    set_exptime(0)

    return -1


def check_wfs_flux():
    slopes_flux_stream = toolbox.open_stream_once(config.Streams.FLUX,
                                                  shm_and_fps_cache)

    if slopes_flux_stream is None:
        logger.error('nuvu', f'{config.Streams.FLUX} is missing')
        return -1

    slopes_flux = slopes_flux_stream.get_data(check=True)

    illuminated_fraction = kalao_tools.wfs_illumination_fraction(
        slopes_flux, config.WFS.illumination_threshold,
        config.WFS.fully_illuminated_subaps)

    return illuminated_fraction > config.WFS.illumination_fraction


def turn_dm_on():
    if ippower.status(config.IPPower.Port.BMC_DM) == IPPowerStatus.OFF:
        logger.info('dm', 'Powering on DM ippower')

        # Avoid safety turning DM off immediately
        time.sleep(1)

        ret = ippower.switch(config.IPPower.Port.BMC_DM, IPPowerStatus.ON)

        if ret != IPPowerStatus.ON:
            logger.error('dm', f'Failed to power on DM ippower')
            return -1

        time.sleep(config.Timers.dm_wait_between_actions)

    bmc_display_fps = toolbox.open_fps_once(config.FPS.BMC, shm_and_fps_cache)

    if bmc_display_fps is not None:
        if not bmc_display_fps.run_runs():
            logger.info('dm', f'Starting {config.FPS.BMC}')

            # Avoid safety turning DM off immediately
            time.sleep(1)

            bmc_display_fps.run_start()

            time.sleep(config.Timers.dm_wait_between_actions)

            reset_dm(config.AO.DM_loop_number)

        if not bmc_display_fps.run_runs():
            logger.error('dm', f'Unable to start {config.FPS.BMC}')

            return -1

    return 0


def turn_dm_off():
    logger.info('dm', 'Turning off DM')

    logger.info('dm', 'Resetting DM')
    reset_dm(config.AO.DM_loop_number)

    time.sleep(config.Timers.dm_wait_between_actions)

    bmc_display_fps = toolbox.open_fps_once(config.FPS.BMC, shm_and_fps_cache)
    if bmc_display_fps is not None:
        logger.info('dm', f'Stopping {config.FPS.BMC}')
        bmc_display_fps.run_stop()

        time.sleep(config.Timers.dm_wait_between_actions)

    logger.info('dm', 'Powering off DM ippower')
    ret = ippower.switch(config.IPPower.Port.BMC_DM, IPPowerStatus.OFF)

    if ret == IPPowerStatus.OFF:
        return 0
    else:
        return -1


def start_wfs_acquisition():
    nuvu_raw_stream = toolbox.open_stream_once(config.Streams.NUVU_RAW,
                                               shm_and_fps_cache)

    if nuvu_raw_stream is None:
        return -1

    # Check if already running
    maqtime = datetime.fromtimestamp(
        nuvu_raw_stream.get_keywords()['_MAQTIME'] / 1e6, tz=timezone.utc)
    if (datetime.now() -
            maqtime).total_seconds() < config.WFS.acquisition_time_timeout:
        return 0

    logger.info('nuvu', 'Starting WFS acquisition')

    _set_tmux_value('nuvu_ctrl', 'SetContinuousAcquisition')

    time.sleep(config.WFS.acquisition_start_wait)

    maqtime = datetime.fromtimestamp(
        nuvu_raw_stream.get_keywords()['_MAQTIME'] / 1e6, tz=timezone.utc)
    if (datetime.now() -
            maqtime).total_seconds() > config.WFS.acquisition_time_timeout:
        logger.info('nuvu', 'Failed to start WFS acquisition')
        return -1

    return 0


def stop_wfs_acquisition():
    logger.info('nuvu', 'Stopping WFS acquisition')

    _set_tmux_value('nuvu_ctrl', 'AbortAcquisition')

    return 0


def stop_wfs():
    logger.info('nuvu', 'Stopping WFS')

    shwfs_process_fps = toolbox.open_fps_once(config.FPS.SHWFS,
                                              shm_and_fps_cache)
    nuvu_acquire_fps = toolbox.open_fps_once(config.FPS.NUVU,
                                             shm_and_fps_cache)

    shwfs_process_was_running = False
    nuvu_acquire_was_running = False

    if shwfs_process_fps is not None:
        if shwfs_process_fps.run_runs():
            shwfs_process_was_running = True

            logger.info('nuvu', f'Stopping {config.FPS.SHWFS}')

            shwfs_process_fps.run_stop()

    if nuvu_acquire_fps is not None:
        if nuvu_acquire_fps.run_runs():
            nuvu_acquire_was_running = True

            logger.info('nuvu', f'Stopping {config.FPS.NUVU}')

            nuvu_acquire_fps.run_stop()

    subprocess.run([
        '/home/kalao/kalao-camstack/scripts/cam-nuvustart', 'stop'
    ])

    Path('/tmp/milk/nuvu_raw.im.shm').unlink(missing_ok=True)

    return nuvu_acquire_was_running, shwfs_process_was_running


def start_wfs(start_nuvu_acquire=True, start_shwfs_process=True):
    logger.info('nuvu', 'Starting WFS')

    shwfs_process_fps = toolbox.open_fps_once(config.FPS.SHWFS,
                                              shm_and_fps_cache)
    nuvu_acquire_fps = toolbox.open_fps_once(config.FPS.NUVU,
                                             shm_and_fps_cache)

    subprocess.run(['/home/kalao/kalao-camstack/scripts/cam-nuvustart'])

    logger.info('nuvu', f'Waiting for nuvu_raw to start')

    if _wait_file('/tmp/milk/nuvu_raw.im.shm') != ReturnCode.OK:
        logger.error('nuvu', f'Timeout while waiting for nuvu_raw')
        return -1

    if nuvu_acquire_fps is not None and start_nuvu_acquire:
        if not nuvu_acquire_fps.run_runs():
            logger.info('nuvu', f'Starting {config.FPS.NUVU}')

            nuvu_acquire_fps.run_start()

            time.sleep(config.AO.wait_fps_run)

        if not nuvu_acquire_fps.run_runs():
            logger.error('nuvu', f'Unable to start {config.FPS.NUVU}')
            return -1

    if shwfs_process_fps is not None and start_shwfs_process:
        if not shwfs_process_fps.run_runs():
            logger.info('nuvu', f'Starting {config.FPS.SHWFS}')

            shwfs_process_fps.run_start()

            time.sleep(config.AO.wait_fps_run)

        if not shwfs_process_fps.run_runs():
            logger.error('nuvu', f'Unable to start {config.FPS.SHWFS}')
            return -1

    return 0


def restart_wfs():
    nuvu_acquire_was_running, shwfs_process_was_running = stop_wfs()
    return start_wfs(nuvu_acquire_was_running, shwfs_process_was_running)


def reset_channel(dm_number, channel, force_flat=False):
    if dm_number == config.AO.DM_loop_number:
        log = 'dm'
    elif dm_number == config.AO.TTM_loop_number:
        log = 'ttm'
    else:
        raise Exception(f'Unknown DM number {dm_number}')

    logger.info(log, f'Resetting channel {channel:02d} of DM {dm_number:02d}')

    stream = f'dm{dm_number:02d}disp{channel:02d}'

    if stream == config.Streams.DM_LOOP or stream == config.Streams.TTM_LOOP:
        mfilt_fps = toolbox.open_fps_once(f'mfilt-{dm_number}',
                                          shm_and_fps_cache)
        if mfilt_fps is not None:
            logger.info(log, f'Zeroing loop {dm_number}')

            mfilt_fps.set_param('loopZERO', True)

    elif stream == config.Streams.DM_FLAT and not force_flat:
        return 0

    stream = toolbox.open_stream_once(stream, shm_and_fps_cache)
    toolbox.zero_stream(stream)

    return 0


def reset_dm(dm_number, force_flat=False):
    if dm_number == config.AO.DM_loop_number:
        log = 'dm'
    elif dm_number == config.AO.TTM_loop_number:
        log = 'ttm'
    else:
        raise Exception(f'Unknown DM number {dm_number}')

    logger.info(log, f'Resetting DM {dm_number:02d}')

    for i in range(0, 12):
        reset_channel(dm_number, i, force_flat=force_flat)

    return 0


def reset_all_dms():
    ret_dm = reset_dm(config.AO.DM_loop_number)
    ret_ttm = reset_dm(config.AO.TTM_loop_number)

    if ret_dm != 0 or ret_ttm != 0:
        return -1
    else:
        return 0


def _set_fps_value(fps_name, key, value):
    fps = toolbox.open_fps_once(fps_name, shm_and_fps_cache)

    if fps is None:
        logger.error('ao', f'Can\'t set {key}, {fps_name} is missing')
        return -1

    return fps.set_param(key, value)


def _set_tmux_value(session, key, value=''):
    server = libtmux.Server()

    try:
        session = server.sessions.get(session_name=session)
        session.attached_pane.send_keys(f'{key}({value})', enter=True)
    except libtmux.exc.TmuxObjectDoesNotExist:
        logger.error('ao', f'Can\'t set {key}, {session} is missing')
        return -1


def _wait_file(file, timeout=30, wait_time=1):
    if not isinstance(file, Path):
        file = Path(file)

    start = time.monotonic()

    while True:
        if file.exists():
            return ReturnCode.OK
        elif (time.monotonic() - start) > timeout:
            return ReturnCode.TIMEOUT

        time.sleep(wait_time)
