#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : com_tools.py
# @Date : 2022-06-13-09-51
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
aocontrol.py is part of the KalAO Instrument Control Software (KalAO-ICS).
"""

import time

import numpy as np

from kalao import logger
from kalao.cacao import toolbox
from kalao.utils import ktools
from kalao.utils.rprint import rprint

from kalao.definitions.enums import LoopStatus, ReturnCode

import config


def close_loops(with_autogain: bool = True) -> LoopStatus:
    """
    Close the primary DM AO loop followed by the secondary TTM loop.

    :return:
    """

    return switch_loops(close=True, with_autogain=with_autogain)


def open_loops(with_autogain: bool = True) -> LoopStatus:
    """
    Open the primary DM AO loop followed by the secondary TTM loop.

    :return:
    """

    return switch_loops(close=False, with_autogain=with_autogain)


def check_loops() -> LoopStatus:
    status = LoopStatus(0)

    dmloop_fps = toolbox.open_fps_once(config.FPS.DMLOOP)

    if dmloop_fps is not None and dmloop_fps.get_param('loopON'):
        status |= LoopStatus.DM_LOOP_ON

    ttmloop_fps = toolbox.open_fps_once(config.FPS.TTMLOOP)

    if ttmloop_fps is not None and ttmloop_fps.get_param('loopON'):
        status |= LoopStatus.TTM_LOOP_ON

    return status


def switch_loops(close: bool = True, with_autogain: bool = True) -> LoopStatus:
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
        switch_loop(i, close, with_autogain=with_autogain)

    return check_loops()


def close_loop(loop_number: int, with_autogain: bool = True) -> LoopStatus:
    return switch_loop(loop_number, close=True, with_autogain=with_autogain)


def open_loop(loop_number: int, with_autogain: bool = True) -> LoopStatus:
    return switch_loop(loop_number, close=False, with_autogain=with_autogain)


def switch_loop(loop_number: int, close: bool = True, autozero: bool = True,
                with_autogain: bool = True) -> LoopStatus:
    """
    Toggle the loop value of one loop

    :return:
    """

    if close:
        logger.info('ao', f'Closing loop {loop_number}')
    else:
        logger.info('ao', f'Opening loop {loop_number}')

    fps_mfilt = toolbox.open_fps_once(f'mfilt-{loop_number}')

    if fps_mfilt is None:
        logger.error('ao', f'mfilt-{loop_number} is missing')

        return LoopStatus.ERROR

    fps_mfilt.set_param('loopON', close)

    if autozero and not close:
        fps_mfilt.set_param('loopZERO', True)

    time.sleep(1)

    if loop_number == 1 and with_autogain:
        switch_autogain(on=close)

    return check_loops()


def autogain_on() -> bool | None:
    return switch_autogain(on=True)


def autogain_off() -> bool | None:
    return switch_autogain(on=False)


def switch_autogain(on=True) -> bool | None:
    return toolbox.set_fps_value(config.FPS.NUVU, 'autogain_on', on)


def set_autogain_setting(setting: int) -> int | None:
    setting = int(setting)

    if setting > config.WFS.max_autogain_setting:
        setting = config.WFS.max_autogain_setting
    elif setting < 0:
        setting = 0

    return toolbox.set_fps_value(config.FPS.NUVU, 'autogain_setting', setting)


def set_emgain(emgain: int = 1, method: str = 'fps') -> int | None:
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
        return toolbox.set_fps_value(config.FPS.NUVU, 'emgain', emgain)
    elif method == 'tmux':
        return toolbox.set_tmux_value('kalaocam_ctrl', 'SetEMCalibratedGain',
                                      emgain)
    else:
        logger.error('ao', f'Unknown method {method} in set_emgain')
        return -1


def set_exptime(exptime: float = 0, method: str = 'fps') -> float | None:
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
        return toolbox.set_fps_value(config.FPS.NUVU, 'exposuretime', exptime)
    elif method == 'tmux':
        return toolbox.set_tmux_value('kalaocam_ctrl', 'SetExposureTime',
                                      exptime)
    else:
        logger.error('ao', f'Unknown method {method} in set_exptime')
        return -1


def emgain_off() -> ReturnCode:
    """
    Completely turn of EM gain on the WFS camera. For double safety the command is sent directly to the tmux as well as
    to the nuvu_acquire fps.

    :return: 0 on success
    """

    ret = ReturnCode.OK

    try:
        toolbox.set_fps_value(config.FPS.NUVU, 'autogain_on', False)
        toolbox.set_fps_value(config.FPS.NUVU, 'autogain_setting', 0)
    except Exception as err:
        rprint(
            f'Can\'t turn off autogain, {config.FPS.NUVU} seems not to be running.'
        )
        rprint(Exception, err)
        ret = ReturnCode.GENERIC_ERROR

    try:
        toolbox.set_fps_value(config.FPS.NUVU, 'emgain', 1)
    except Exception as err:
        rprint(
            f'Can\'t turn off emgain, {config.FPS.NUVU} seems not to be running.'
        )
        rprint(Exception, err)
        ret = ReturnCode.GENERIC_ERROR

    try:
        toolbox.set_tmux_value('kalaocam_ctrl', 'SetEMCalibratedGain', 1)
    except Exception as err:
        rprint(f'Can\'t turn off emgain, nucu_ctrl seems not to be running.')
        rprint(Exception, err)
        ret = ReturnCode.GENERIC_ERROR

    return ret


def set_dmloop_gain(gain: float) -> float | None:
    return toolbox.set_fps_value(config.FPS.DMLOOP, 'loopgain', gain)


def set_dmloop_mult(mult: float) -> float | None:
    return toolbox.set_fps_value(config.FPS.DMLOOP, 'loopmult', mult)


def set_dmloop_limit(limit) -> float | None:
    return toolbox.set_fps_value(config.FPS.DMLOOP, 'looplimit', limit)


def dmloop_zero() -> bool | None:
    return toolbox.set_fps_value(config.FPS.DMLOOP, 'loopZERO', True)


def set_ttmloop_gain(gain: float) -> float | None:
    return toolbox.set_fps_value(config.FPS.TTMLOOP, 'loopgain', gain)


def set_ttmloop_mult(mult: float) -> float | None:
    return toolbox.set_fps_value(config.FPS.TTMLOOP, 'loopmult', mult)


def set_ttmloop_limit(limit: float) -> float | None:
    return toolbox.set_fps_value(config.FPS.TTMLOOP, 'looplimit', limit)


def ttmloop_zero() -> bool | None:
    return toolbox.set_fps_value(config.FPS.TTMLOOP, 'loopZERO', True)


def set_modalgains(modalgains: np.ndarray,
                   stream_name: str = config.Streams.MODALGAINS) -> int:
    modalgains_stream = toolbox.open_stream_once(stream_name)

    delta = modalgains_stream.shape[0] - modalgains.shape[0]

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


def set_dm_max_stroke(max_stroke: float) -> float | None:
    return toolbox.set_fps_value(config.FPS.BMC, 'max_stroke', max_stroke)


def set_dm_stroke_mode(stroke_mode: int) -> int | None:
    return toolbox.set_fps_value(config.FPS.BMC, 'stroke_mode', stroke_mode)


def set_dm_target_stroke(target_stroke: float) -> float | None:
    return toolbox.set_fps_value(config.FPS.BMC, 'target_stroke',
                                 target_stroke)


def optimize_wfs_flux() -> ReturnCode:
    # Check if we are already good
    if check_wfs_flux():
        return ReturnCode.OK

    nuvu_acquire_fps = toolbox.open_fps_once(config.FPS.NUVU)

    if nuvu_acquire_fps is None:
        logger.error('wfs', f'{config.FPS.NUVU} is missing')
        return ReturnCode.GENERIC_ERROR

    nuvu_acquire_fps.set_param('autogain_on', True)

    timeout = time.monotonic() + config.AO.flux_stabilization_timeout

    prev_setting = -1
    prev_timestamp = time.monotonic()

    while time.monotonic() < timeout:
        setting = nuvu_acquire_fps.get_param('autogain_setting')
        timestamp = time.monotonic()

        if setting != prev_setting:
            prev_setting = setting
            prev_timestamp = timestamp

        elif timestamp - prev_timestamp >= config.AO.flux_stabilization_time:
            if check_wfs_flux():
                return ReturnCode.OK
            else:
                break

    # Reset values if no signal detected
    nuvu_acquire_fps.set_param('autogain_setting', 0)
    set_emgain(1)
    set_exptime(0)

    return ReturnCode.TIMEOUT


def check_wfs_flux() -> bool:
    flux_stream = toolbox.open_stream_once(config.Streams.FLUX)

    if flux_stream is None:
        logger.error('wfs', f'{config.Streams.FLUX} is missing')
        return False

    flux = []
    for i in range(config.AO.flux_avg):
        flux.append(flux_stream.get_data(check=True))

    illuminated_fraction = ktools.wfs_illumination_fraction(
        np.mean(np.array(flux), axis=0), config.WFS.illumination_threshold,
        config.WFS.fully_illuminated_subaps)

    return illuminated_fraction > config.WFS.illumination_fraction


def reset_channel(dm_number: int, channel: int,
                  force_flat: bool = False) -> ReturnCode:
    if dm_number == config.AO.DM_loop_number:
        log = 'dm'
    elif dm_number == config.AO.TTM_loop_number:
        log = 'ttm'
    else:
        raise Exception(f'Unknown DM number {dm_number}')

    logger.info(log, f'Resetting channel {channel:02d} of DM {dm_number:02d}')

    stream = f'dm{dm_number:02d}disp{channel:02d}'

    if stream == config.Streams.DM_LOOP or stream == config.Streams.TTM_LOOP:
        mfilt_fps = toolbox.open_fps_once(f'mfilt-{dm_number}')
        if mfilt_fps is not None:
            logger.info(log, f'Zeroing loop {dm_number}')

            mfilt_fps.set_param('loopZERO', True)

    elif stream == config.Streams.DM_FLAT and not force_flat:
        return ReturnCode.OK

    stream = toolbox.open_stream_once(stream)
    toolbox.zero_stream(stream)

    return ReturnCode.OK


def reset_dm(dm_number: int, force_flat: bool = False) -> ReturnCode:
    ok = True

    if dm_number == config.AO.DM_loop_number:
        log = 'dm'
    elif dm_number == config.AO.TTM_loop_number:
        log = 'ttm'
    else:
        raise Exception(f'Unknown DM number {dm_number}')

    logger.info(log, f'Resetting DM {dm_number:02d}')

    for i in range(0, 12):
        if reset_channel(dm_number, i, force_flat=force_flat) != ReturnCode.OK:
            ok = False

    if ok:
        return ReturnCode.OK
    else:
        return ReturnCode.GENERIC_ERROR


def reset_all_dms() -> ReturnCode:
    ret_dm = reset_dm(config.AO.DM_loop_number)
    ret_ttm = reset_dm(config.AO.TTM_loop_number)

    if ret_dm == ReturnCode.OK and ret_ttm == ReturnCode.OK:
        return ReturnCode.OK
    else:
        return ReturnCode.GENERIC_ERROR
