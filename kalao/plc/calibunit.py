#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : calibunit
# @Date : 2021-01-02-14-36
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
calibunit.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""
import math

import numpy as np

from kalao import logger
from kalao.plc import core

from opcua import Client

from kalao.definitions.enums import PLCStatus, ReturnCode

import config


def move_to_tungsten_position() -> float:
    """
    Move calibration unit to the position where the tungsten lamp is

    :return: position of the calibration unit
    """

    new_position = move(config.Tungsten.position)

    if math.isclose(new_position, config.Tungsten.position, abs_tol=0.1):
        return new_position
    else:
        logger.error(
            'calibunit',
            f'Calibration unit position requested {config.Tungsten.position} but moved to {new_position}'
        )
        return np.nan


def move_to_laser_position() -> float:
    """
    Move calibration unit to the position where the laser lamp is

    :return: position of the calibration unit
    """

    new_position = move(config.Laser.position)

    if math.isclose(new_position, config.Laser.position, abs_tol=0.1):
        return new_position
    else:
        logger.error(
            'calibunit',
            f'Calibration unit position requested {config.Laser.position} but moved to {new_position}'
        )
        return np.nan


def move(position: float, velocity: float = config.CalibUnit.velocity,
         blocking: bool = True, beck: Client = None) -> float:
    """
    Move the calibration unit to position
    """

    if position < config.CalibUnit.position_min:
        logger.warn(
            'calibunit',
            f'Position {position} mm lower than minimal position {config.CalibUnit.position_min} mm, clipping.'
        )
        position = config.CalibUnit.position_min

    elif position > config.CalibUnit.position_max:
        logger.warn(
            'calibunit',
            f'Position {position} mm higher than maximal position {config.CalibUnit.position_max} mm, clipping.'
        )
        position = config.CalibUnit.position_max

    logger.info(
        'calibunit',
        f'Moving calibration unit to position {position} mm at {velocity} mm/s'
    )

    new_position = core.motor_move(config.PLC.Node.CALIB_UNIT, position,
                                   velocity, blocking, beck=beck)

    if blocking:
        logger.info('calibunit',
                    f'Moved calibration unit to position {new_position} mm')

    return new_position


@core.beckhoff_autoconnect
def stop(beck: Client = None) -> None:
    logger.info('calibunit', f'Stopping calibration unit')
    core.motor_send_stop(config.PLC.Node.CALIB_UNIT, beck=beck)


@core.beckhoff_autoconnect
def wait_move(beck: Client = None) -> int:
    core.wait_loop(f'Waiting for calibration unit movement',
                   lambda: is_moving(beck=beck), 5)

    return 0


def get_position(beck: Client = None) -> float:
    position = core.motor_get_position(config.PLC.Node.CALIB_UNIT, beck=beck)

    if np.isnan(position):
        error_code, error_text = core.get_error(config.PLC.Node.CALIB_UNIT,
                                                beck=beck)
        logger.error('calibunit', f'{error_text} ({error_code})')

    return position


def is_moving(beck: Client = None) -> bool:
    return core.motor_is_moving(config.PLC.Node.CALIB_UNIT, beck=beck)


@core.beckhoff_autoconnect
def init(force_init: bool = True, beck: Client = None) -> ReturnCode:
    '''
    Initialise the calibration unit.
    '''

    logger.info('calibunit', 'Initialising calibration unit')

    ret_init = core.motor_init(config.PLC.Node.CALIB_UNIT, force_init,
                               beck=beck)

    if ret_init != ReturnCode.PLC_INIT_SUCCESS:
        logger.error('calibunit', f'Calibration unit initialisation failed')
    else:
        logger.info('calibunit', 'Calibration unit initialised')

        if config.PLC.Node.CALIB_UNIT in config.PLC.initial_pos:
            move(config.PLC.initial_pos[config.PLC.Node.CALIB_UNIT], beck=beck)

    return ret_init


def get_state(beck: Client = None) -> PLCStatus:
    return core.motor_get_status(config.PLC.Node.CALIB_UNIT, beck=beck)
