#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : adc.py
# @Date : 2021-08-12-12-00
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
adc.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import time
from enum import IntEnum

import numpy as np
from scipy.optimize import minimize_scalar

from kalao import database, euler, logger
from kalao.plc import core, filterwheel
from kalao.utils import atmosphere

from kalao.definitions.enums import ReturnCode, TrackingStatus

import config


class ADCCommand(IntEnum):
    MAX_DISP = 0
    ZERO_DISP = 180


def get_optimal_adc_angle(zenith_angle, wavelength, T, P, H):
    target_dispersion = atmosphere.air_dispersion(
        zenith_angle, wavelength, T, P, H) - atmosphere.air_dispersion(
            zenith_angle, config.ADC.dispersion_reference_wavelength, T, P, H)
    dispersion = config.ADC.dispersion[wavelength]

    res = minimize_scalar(lambda x: np.abs(dispersion(x) - target_dispersion),
                          bounds=(0, 180))

    if res.success and res.fun < 1e-2:
        return res.x
    else:
        return 0


def configure(beck=None, override_threshold=False):
    if euler.telescope_tracking() == TrackingStatus.IDLE:
        logger.warn('adc', 'Configuring ADC while telescope is not tracking')

    filter_name = filterwheel.get_filter(type=str, from_db=True)
    T = euler.outside_temperature()
    P = euler.outside_pressure()
    H = euler.outside_hygrometry()
    zenith_angle = euler.telescope_zenith_angle()

    wavelength = config.FilterWheel.filter_to_wavelength[filter_name]

    # TODO: in case if filter_name is not in filter_to_wavelength

    if type(wavelength) == list:
        angle = 0

        for w in wavelength:
            angle += get_optimal_adc_angle(zenith_angle, w, T, P, H)

        angle /= len(wavelength)
    else:
        angle = get_optimal_adc_angle(zenith_angle, wavelength, T, P, H)

    if override_threshold or np.abs(angle -
                                    get_angle()) > config.ADC.angle_threshold:
        set_angle(angle, beck=beck)

    return 0


def set_max_disp(beck=None):
    return set_angle(ADCCommand.MAX_DISP, beck=beck)


def set_zero_disp(beck=None):
    return set_angle(ADCCommand.ZERO_DISP, beck=beck)


def set_angle(angle, beck=None):
    logger.info('adc', f'Setting angle between ADC prisms to {angle}°')

    # Motors are face to face, offset by same angle so they are counter-rotating
    rotate(config.PLC.Node.ADC1, config.ADC.max_disp_angle_1 + angle/2,
           wait=False, beck=beck)
    rotate(config.PLC.Node.ADC2, config.ADC.max_disp_angle_2 + angle/2,
           wait=False, beck=beck)

    time.sleep(2)

    wait_rotate_both(beck=beck)

    # TODO: check motors moved successfully
    database.store('obs', {'adc_angle': angle})

    return angle


def get_angle():
    angle = database.get_last_value('obs', 'adc_angle')

    if angle is None:
        return np.inf
    else:
        return angle


def rotate(node, position, velocity=config.ADC.velocity, wait=True, beck=None):
    logger.info('adc',
                f'Moving ADC {node} to position {position}° at {velocity}°/s')

    new_position = core.motor_move(node, position, velocity, wait, beck=beck)

    if wait:
        logger.info('adc', f'Moved ADC {node} to position {new_position}°')

    return new_position


@core.beckhoff_autoconnect
def wait_rotate(node, beck=None):
    core.wait_loop(f'Waiting for ADC {node} rotation',
                   lambda: is_moving(node, beck=beck), 5)

    return 0


def wait_rotate_both(beck=None):
    wait_rotate(config.PLC.Node.ADC1, beck=beck)
    wait_rotate(config.PLC.Node.ADC2, beck=beck)

    return 0


def get_position(node, beck=None):
    position = core.motor_get_position(node, beck=beck)

    if np.isnan(position):
        error_code, error_text = core.get_error(node, beck=beck)
        logger.error('adc', f'{error_text} ({error_code})')

    return position


def is_moving(node, beck=None):
    return core.motor_is_moving(node, beck=beck)


@core.beckhoff_autoconnect
def init(node, force_init=False, beck=None):
    """
    Initialise the ADC motor.
    """
    logger.info('adc', f'Initialising ADC {node}')

    ret_init = core.motor_init(node, force_init, beck=beck)

    if ret_init != ReturnCode.PLC_INIT_SUCCESS:
        logger.error('adc', f'ADC {node} initialisation failed')
    else:
        logger.info('adc', f'ADC {node} initialised')

        if node in config.PLC.initial_pos:
            rotate(node, config.PLC.initial_pos[node], beck=beck)

    return ret_init


def get_state(node, beck=None):
    return core.motor_get_status(node, beck=beck)
