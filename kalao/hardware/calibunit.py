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

from opcua import Client

from kalao import logger
from kalao.hardware import plc

from kalao.definitions.enums import (CalibUnitPositionName, PLCStatus,
                                     ReturnCode)

import config


def move_to_tungsten_position() -> float:
    """
    Move calibration unit to the position where the tungsten lamp is

    :return: position of the calibration unit
    """

    new_position = move(config.Tungsten.position)

    if get_position_name(position=new_position, tolerance=config.CalibUnit.
                         tolerance_move) == CalibUnitPositionName.TUNGSTEN:
        return new_position
    else:
        logger.error(
            'calibunit',
            f'Calibration unit position requested {config.Tungsten.position:.2f} but moved to {new_position:.2f}'
        )
        return np.nan


def move_to_laser_position() -> float:
    """
    Move calibration unit to the position where the laser lamp is

    :return: position of the calibration unit
    """

    new_position = move(config.Laser.position)

    if get_position_name(position=new_position, tolerance=config.CalibUnit.
                         tolerance_move) == CalibUnitPositionName.LASER:
        return new_position
    else:
        logger.error(
            'calibunit',
            f'Calibration unit position requested {config.Laser.position:.2f} but moved to {new_position:.2f}'
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
            f'Position {position:.2f} mm lower than minimal position {config.CalibUnit.position_min:.2f} mm, clipping.'
        )
        position = config.CalibUnit.position_min

    elif position > config.CalibUnit.position_max:
        logger.warn(
            'calibunit',
            f'Position {position:.2f} mm higher than maximal position {config.CalibUnit.position_max:.2f} mm, clipping.'
        )
        position = config.CalibUnit.position_max

    logger.info(
        'calibunit',
        f'Moving calibration unit to position {position:.2f} mm at {velocity:.2f} mm/s'
    )

    new_position = plc.motor_move(config.PLC.Node.CALIB_UNIT, position,
                                  velocity, blocking, beck=beck)

    if blocking:
        logger.info(
            'calibunit',
            f'Moved calibration unit to position {new_position:.2f} mm')

    return new_position


@plc.autoconnect
def stop(beck: Client = None) -> None:
    logger.info('calibunit', 'Stopping calibration unit')
    plc.motor_send_stop(config.PLC.Node.CALIB_UNIT, beck=beck)


@plc.autoconnect
def wait(beck: Client = None) -> int:
    plc.wait_loop(lambda: is_moving(beck=beck), 5)

    return 0


def get_position(beck: Client = None) -> float:
    position = plc.motor_get_position(config.PLC.Node.CALIB_UNIT, beck=beck)

    if np.isnan(position):
        error_code, error_text = plc.get_error(config.PLC.Node.CALIB_UNIT,
                                               beck=beck)
        logger.error('calibunit', f'{error_text} ({error_code})')

    return position


def get_position_name(position=None, tolerance=config.CalibUnit.tolerance_disp,
                      beck: Client = None) -> CalibUnitPositionName:
    if position is None:
        position = get_position(beck=beck)

    if np.isnan(position):
        return CalibUnitPositionName.ERROR
    elif math.isclose(position, config.Laser.position, abs_tol=tolerance,
                      rel_tol=0):
        return CalibUnitPositionName.LASER
    elif math.isclose(position, config.Tungsten.position, abs_tol=tolerance,
                      rel_tol=0):
        return CalibUnitPositionName.TUNGSTEN
    else:
        return CalibUnitPositionName.UNKNOWN


def is_moving(beck: Client = None) -> bool:
    return plc.motor_get_status(config.PLC.Node.CALIB_UNIT,
                                beck=beck) == PLCStatus.MOVING


@plc.autoconnect
def init(force_init: bool = False, beck: Client = None) -> ReturnCode:
    '''
    Initialise the calibration unit.
    '''

    logger.info('calibunit', 'Initialising calibration unit')

    ret_init = plc.motor_init(config.PLC.Node.CALIB_UNIT,
                              force_init=force_init, beck=beck)

    if ret_init != ReturnCode.HW_INIT_SUCCESS:
        logger.error('calibunit', 'Calibration unit initialisation failed')
    else:
        logger.info('calibunit', 'Calibration unit initialised')

        if config.PLC.Node.CALIB_UNIT in config.PLC.initial_state:
            move(config.PLC.initial_state[config.PLC.Node.CALIB_UNIT],
                 beck=beck)

    return ret_init


def get_status(beck: Client = None) -> PLCStatus:
    return plc.motor_get_status(config.PLC.Node.CALIB_UNIT, beck=beck)
