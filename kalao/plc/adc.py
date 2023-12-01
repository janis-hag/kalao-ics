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

adc_name = {1: 'ADC1_Newport_PR50PP.motor', 2: 'ADC2_Newport_PR50PP.motor'}

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
def air_refractive_index_EDLEN(lambda0_, T, P, H=None):
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
    rotate(
        1, position=config.ADC.max_disp_angle_1 + config.ADC.max_disp_offset +
        angle/2, beck=beck)
    rotate(
        2, position=config.ADC.max_disp_angle_2 - config.ADC.max_disp_offset +
        angle/2, beck=beck)

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


@core.beckhoff_autoconnect
def rotate(adc_id, position=0, beck=None):
    # define commands
    motor_nCommand = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                   ".ctrl.nCommand")
    motor_bExecute = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                   ".ctrl.bExecute")

    # Check if initialised
    init_result = init(adc_id, force_init=False, beck=beck,
                       motor_nCommand=motor_nCommand,
                       motor_bExecute=motor_bExecute)
    if not init_result == 0:
        return init_result

    # Set velocity to 1 in case is has been changed
    motor_lrVelocity = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                     ".ctrl.lrVelocity")
    motor_lrVelocity.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(float(1),
                       motor_lrVelocity.get_data_type_as_variant_type())))
    motor_lrPosition = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                     ".ctrl.lrPosition")

    if isinstance(position, numbers.Number):
        # Set target position
        motor_lrPosition.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                ua.Variant(float(position),
                           motor_lrPosition.get_data_type_as_variant_type())))
        # Set move command
        motor_nCommand.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                ua.Variant(int(3),
                           motor_nCommand.get_data_type_as_variant_type())))
        # Execute
        send_execute(motor_bExecute)

        #TODO: We don't wait for position, so what to do with new_position?

        # Get new position
        new_position = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                     ".stat.lrPosActual").get_value()
        # motor_lrPosition = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".ctrl.lrPosition")
    else:
        database.store(
            'obs', {
                'calib_unit_log':
                    f'Expected position to be a number, received: {position}'
            })
        new_position = -1

    return new_position


@core.beckhoff_autoconnect
def wait_rotate(adc_id, beck=None):
    core.wait_loop(
        f'Waiting for ADC {adc_id} rotation',
        lambda: beck.get_node(f"ns=4; s=MAIN.{adc_name[adc_id]}.stat.sStatus"
                              ).get_value().startswith('MOVING'), 5)

    return 0


def wait_rotate_both(beck=None):
    wait_rotate(1, beck=beck)
    wait_rotate(2, beck=beck)

    return 0


def plc_status(adc_id, beck=None):
    """
    Query the status of the ADC motor.

    :return: complete status of calibration unit
    """

    return core.device_status(adc_name[adc_id], beck=beck)


@core.beckhoff_autoconnect
def check_error(adc_id, beck=None):
    if beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                     ".stat.sErrorText").get_value() == 0:
        adc_status = 0
    else:
        adc_status = 'ERROR'

    return adc_status


@core.beckhoff_autoconnect
def init(adc_id, force_init=False, beck=None, motor_nCommand=None,
         motor_bExecute=None):
    """
    Initialise the ADC motor.

    :param motor_bExecute:
    :param adc_id:
    :param force_init:
    :param beck: the handle for the plc connection
    :param motor_nCommand: handle to send commands to the motor
    :return: returns 0 on success and error code on failure
    """
    database.store('obs', {'adc_log': f'Initialising ADC {adc_id}'})

    init_status = 0

    if motor_nCommand is None:
        # define commands
        motor_nCommand = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                       ".ctrl.nCommand")

    if motor_bExecute is None:
        motor_bExecute = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                       ".ctrl.bExecute")

    # Check if enabled, if no do enable
    if not beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                         ".stat.bEnabled").get_value() or force_init:
        motor_bEnable = beck.get_node("ns = 4; s = MAIN." + adc_name[adc_id] +
                                      ".ctrl.bEnable")
        motor_bEnable.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                ua.Variant(True,
                           motor_bEnable.get_data_type_as_variant_type())))
        if not beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                             ".stat.bEnabled").get_value():
            error = '[ERROR] ' + str(
                beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                              ".stat.nErrorCode").get_value())
            init_status = error

    # Check if init, if not do init
    if not beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                         ".stat.bInitialised").get_value() or force_init:
        send_init(motor_nCommand, motor_bExecute)

        sleep(15)
        core.wait_loop(
            f'Waiting for ADC {adc_id} initialisation', lambda: beck.get_node(
                f"ns=4; s=MAIN.{adc_name[adc_id]}.stat.sStatus").get_value().
            startswith('INITIALISING'), 5)

        if not beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                             ".stat.bInitialised").get_value():
            error = '[ERROR] ' + str(
                beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                              ".stat.nErrorCode").get_value())
            init_status = error

    return init_status


def send_execute(motor_bExecute):
    motor_bExecute.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, motor_bExecute.get_data_type_as_variant_type())))


def send_init(motor_nCommand, motor_bExecute):
    motor_nCommand.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(int(1),
                       motor_nCommand.get_data_type_as_variant_type())))
    # Execute
    send_execute(motor_bExecute)
