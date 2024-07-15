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

from kalao import logger, services
from kalao.cacao import toolbox

from kalao.definitions.enums import LoopStatus, ReturnCode, ServiceAction

import config


def close_loops(with_autogain: bool = True) -> LoopStatus:
    """
    Close the primary DM AO loop followed by the secondary TTM loop.

    :return:
    """

    return switch_loops(close=True, with_autogain=with_autogain)


def open_loops(autozero: bool = True,
               with_autogain: bool = True) -> LoopStatus:
    """
    Open the primary DM AO loop followed by the secondary TTM loop.

    :return:
    """

    return switch_loops(close=False, autozero=autozero,
                        with_autogain=with_autogain)


def check_loops() -> LoopStatus:
    status = LoopStatus(0)

    dmloop_fps = toolbox.open_fps_once(config.FPS.DMLOOP)

    if dmloop_fps is not None and dmloop_fps.run_isrunning(
    ) and dmloop_fps.get_param('loopON'):
        status |= LoopStatus.DM_LOOP_ON

    ttmloop_fps = toolbox.open_fps_once(config.FPS.TTMLOOP)

    if ttmloop_fps is not None and ttmloop_fps.run_isrunning(
    ) and ttmloop_fps.get_param('loopON'):
        status |= LoopStatus.TTM_LOOP_ON

    return status


def switch_loops(close: bool = True, autozero: bool = True,
                 with_autogain: bool = True) -> LoopStatus:
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
        switch_loop(i, close, autozero=autozero, with_autogain=with_autogain)

    return check_loops()


def close_loop(loop_number: int, with_autogain: bool = True) -> LoopStatus:
    return switch_loop(loop_number, close=True, with_autogain=with_autogain)


def open_loop(loop_number: int, autozero: bool = True,
              with_autogain: bool = True) -> LoopStatus:
    return switch_loop(loop_number, close=False, autozero=autozero,
                       with_autogain=with_autogain)


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

    services.unit_control(config.Systemd.services['Monitoring Timer']['unit'],
                          ServiceAction.RELOAD)

    return check_loops()


def autogain_on() -> bool | None:
    return switch_autogain(on=True)


def autogain_off() -> bool | None:
    return switch_autogain(on=False)


def switch_autogain(on=True) -> bool | None:
    return toolbox.set_fps_value(config.FPS.NUVU, 'autogain_on', on)


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
                   shm_name: str = config.SHM.MODALGAINS) -> int:
    modalgains_shm = toolbox.open_shm_once(shm_name)

    delta = modalgains_shm.shape[0] - modalgains.shape[0]

    if modalgains_shm is not None:
        if delta < 0:
            modalgains_shm.set_data(modalgains[:delta], True)
        elif delta > 0:
            modalgains_shm.set_data(
                np.pad(modalgains, (0, delta), constant_values=0), True)
        else:
            modalgains_shm.set_data(modalgains, True)

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


def reset_channel(dm_number: int, channel: int,
                  force_flat: bool = False) -> ReturnCode:
    if dm_number == config.AO.DM_loop_number:
        log = 'dm'
    elif dm_number == config.AO.TTM_loop_number:
        log = 'ttm'
    else:
        raise Exception(f'Unknown DM number {dm_number}')

    logger.info(log, f'Resetting channel {channel:02d} of DM {dm_number:02d}')

    shm_name = f'dm{dm_number:02d}disp{channel:02d}'

    if shm_name == config.SHM.DM_LOOP or shm_name == config.SHM.TTM_LOOP:
        mfilt_fps = toolbox.open_fps_once(f'mfilt-{dm_number}')
        if mfilt_fps is not None:
            logger.info(log, f'Zeroing loop {dm_number}')

            mfilt_fps.set_param('loopZERO', True)

    elif shm_name == config.SHM.DM_FLAT and not force_flat:
        return ReturnCode.OK

    shm = toolbox.open_shm_once(shm_name)
    toolbox.zero_stream(shm)

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
