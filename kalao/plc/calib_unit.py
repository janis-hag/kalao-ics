#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : calib_unit
# @Date : 2021-01-02-14-36
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
calib_unit.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import numpy as np

from kalao.plc import core
from kalao.utils import database

import config


def move_to_tungsten_position():
    """
    Move calibration unit to the position where the tungsten lamp is

    :return: position of the calibration unit
    """

    new_position = move(config.Tungsten.position)

    if abs(new_position - config.Tungsten.position) < 0.1:
        return new_position
    else:
        database.store(
            'obs', {
                'calib_unit_log':
                    f'[ERROR] Calibration unit position requested {config.Tungsten.position} but moved to {new_position}'
            })
        return np.nan


def move_to_laser_position():
    """
    Move calibration unit to the position where the laser lamp is

    :return: position of the calibration unit
    """

    new_position = move(config.Laser.position)

    if abs(new_position - config.Laser.position) < 0.1:
        return new_position
    else:
        database.store(
            'obs', {
                'calib_unit_log':
                    f'[ERROR] Calibration unit position requested {config.Laser.position} but moved to {new_position}'
            })
        return np.nan


def move_px(pixel, absolute=False):
    """
    Move calib unit by amount of pixels

    :param pixel: pixel to move to
    :return:
    """

    if absolute and pixel < 0:
        database.store('obs', {
            'calib_unit_log':
                '[ERROR] Calib unit position should not be negative'
        })
        return np.nan

    current_position = get_position()

    if absolute:
        position = config.CalibUnit.initial_offset + config.CalibUnit.px_to_mm * pixel
    else:
        position = current_position + config.CalibUnit.px_to_mm * pixel

    new_position = move(position)

    return new_position


def move(position, velocity=config.CalibUnit.velocity, wait=True, beck=None):
    """
    Move the calibration unit to position
    """

    if position < config.CalibUnit.position_min:
        database.store(
            'obs', {
                'calib_unit_log':
                    f'[WARNING] Position {position}mm lower than minimal position {config.CalibUnit.position_min}mm, clipping.'
            })
        position = config.CalibUnit.position_min

    elif position > config.CalibUnit.position_max:
        database.store(
            'obs', {
                'calib_unit_log':
                    f'[WARNING] Position {position}mm higher than maximal position {config.CalibUnit.position_max}mm, clipping.'
            })
        position = config.CalibUnit.position_max

    database.store(
        'obs', {
            'calib_unit_log':
                f'Moving calibration unit to position {position}mm at {velocity}mm/s'
        })

    new_position = core.motor_move(config.PLC.Node.CALIB_UNIT, position,
                                   velocity, wait, beck=beck)

    if wait:
        database.store(
            'obs', {
                'calib_unit_log':
                    f'Moved calibration unit to position {new_position}mm'
            })

    return new_position


@core.beckhoff_autoconnect
def wait_move(beck=None):
    core.wait_loop(f'Waiting for calibration unit movement',
                   lambda: is_moving(beck=beck), 5)

    return 0


def get_position(beck=None):
    position = core.motor_get_position(config.PLC.Node.CALIB_UNIT, beck=beck)

    if np.isnan(position):
        error_code, error_text = core.get_error(config.PLC.Node.CALIB_UNIT,
                                                beck=beck)
        database.store('obs', {
            'calib_unit_log': f'[ERROR] {error_text} ({error_code})'
        })

    return position


def is_moving(beck=None):
    return core.motor_is_moving(config.PLC.Node.CALIB_UNIT, beck=beck)


@core.beckhoff_autoconnect
def init(force_init=True, beck=None):
    '''
    Initialise the calibration unit.
    '''

    database.store('obs', {'calib_unit_log': 'Initialising calibration unit'})

    ret_init = core.motor_init(config.PLC.Node.CALIB_UNIT, force_init,
                               beck=beck)

    if config.PLC.Node.CALIB_UNIT in config.PLC.initial_pos:
        move(config.PLC.initial_pos[config.PLC.Node.CALIB_UNIT], beck=beck)

    return ret_init


def get_state(beck=None):
    return core.motor_get_status(config.PLC.Node.CALIB_UNIT, beck=beck)
