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

import numbers
from enum import IntEnum
from time import sleep

import numpy as np
from scipy.optimize import minimize_scalar

from kalao import euler
from kalao.plc import core, filterwheel
from kalao.utils import database

from opcua import ua

from kalao.definitions.enums import TrackingStatus

import config

adc_node = {1: 'ADC1_Newport_PR50PP.motor', 2: 'ADC2_Newport_PR50PP.motor'}

# Conventions:
# Temperature in K
# Pressure in Pa
# Hygrometry between 0 and 1


class ADCCommand(IntEnum):
    MAX_DISP = 0
    ZERO_DISP = 180


# Owens 1967 formula
def air_refractive_index_OWENS(lambda0_, T, P, H):
    sig = 1. / (lambda0_*1e6)
    P = P / 100
    t = T - 273.15

    Pw_sat = 6.11 * 10**((7.5*t) / (t+237.7))
    Pw = Pw_sat * H
    Ps = P - Pw

    Ds = Ps / T * (1 + Ps * (57.90e-8 - 9.3250e-4/T + 0.25844 / T**2))
    Dw = Pw / T * (
        1 + Pw * (1 + 3.70e-4*Pw) *
        (-2.37321e-3 + 2.23366/T - 710.792 / T**2 + 7.75141e4 / T**3))

    n = (2371.34 + 683939.7 / (130. - sig**2) + 4547.3 /
         (38.9 - sig**2)) * Ds + (6487.31 + 58.058 * sig**2 -
                                  0.71150 * sig**4 + 0.08851 * sig**6) * Dw

    return 1 + n*1e-8


# Edlen 1966 formula
def air_refractive_index_EDLEN(lambda0_, T, P, _):
    sig = 1. / (lambda0_*1e6)
    p = P / 101325 * 760
    t = T - 273.15

    n = 8342.13 + 2406030 / (130. - sig**2) + 15997. / (38.9 - sig**2)
    n *= 0.00138823 * p / (1 + 0.003671*t)

    return 1 + n*1e-8


def dispersion_air(zenith_angle, wavelength, T, P, H,
                   air_refractive_index=air_refractive_index_EDLEN):
    return np.tan(zenith_angle * np.pi / 180) * (
        air_refractive_index(wavelength, T, P, H) -
        air_refractive_index(config.ADC.dispersion_reference_wavelength, T, P,
                             H)) * 180 / np.pi * 3600


def get_optimal_adc_angle(zenith_angle, wavelength, T, P, H):
    target_dispersion = dispersion_air(zenith_angle, wavelength, T, P, H)
    dispersion = config.ADC.dispersion[wavelength]

    res = minimize_scalar(lambda x: np.abs(dispersion(x) - target_dispersion),
                          bounds=(0, 180))

    if res.success and res.fun < 1e-2:
        return res.x
    else:
        return 0


def configure(beck=None, override_threshold=False):
    if euler.telescope_tracking() == TrackingStatus.IDLE:
        database.store('obs', {
            'adc_log':
                '[WARNING] Configuring ADC while telescope is not tracking'
        })

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
    database.store('obs', {
        'adc_log': f'Setting angle between ADC prisms to {angle}°'
    })

    # Motors are face to face, offset by same angle so they are counter-rotating
    rotate(1, config.ADC.max_disp_angle_1 + angle/2, wait=False, beck=beck)
    rotate(2, config.ADC.max_disp_angle_2 + angle/2, wait=False, beck=beck)

    sleep(2)

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


def rotate(adc_id, position, velocity=config.ADC.velocity, wait=True,
           beck=None):
    database.store('obs', {
        'adc_log':
            f'Moving ADC {adc_id} to position {position}° at {velocity}°/s'
    })

    new_position = core.motor_move('Linear_Standa_8MT', position, velocity,
                                   wait, beck=beck)

    if wait:
        database.store('obs', {
            'adc_log': f'Moved ADC {adc_id} to position {new_position}°'
        })

    return new_position


@core.beckhoff_autoconnect
def wait_rotate(adc_id, beck=None):
    core.wait_loop(f'Waiting for ADC {adc_id} rotation',
                   lambda: is_moving(adc_id, beck=beck), 5)

    return 0


def wait_rotate_both(beck=None):
    wait_rotate(1, beck=beck)
    wait_rotate(2, beck=beck)

    return 0


def get_position(adc_id, beck=None):
    position = core.motor_get_position(adc_node[adc_id], beck=beck)

    if np.isnan(position):
        error_code, error_text = core.get_error(adc_node[adc_id], beck=beck)
        database.store('obs',
                       {'adc_log': f'[ERROR] {error_text} ({error_code})'})

    return position


def is_moving(adc_id, beck=None):
    return core.motor_is_moving(adc_node[adc_id], beck=beck)


@core.beckhoff_autoconnect
def init(adc_id, force_init=False, beck=None):
    """
    Initialise the ADC motor.
    """
    database.store('obs', {'adc_log': f'Initialising ADC {adc_id}'})

    init_ret = core.motor_init(adc_node[adc_id], force_init, beck=beck)

    if f'adc_{adc_id}' in config.PLC.initial_pos:
        rotate(adc_id, config.PLC.initial_pos[f'adc_{adc_id}'], beck=beck)

    return init_ret


def get_plc_status(beck=None):
    return core.motor_get_status(beck=beck)
