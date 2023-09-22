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
import numpy as np
from opcua import ua
from time import sleep
from configparser import ConfigParser
from pathlib import Path
import os

from numpy.polynomial import Polynomial
from scipy.optimize import minimize_scalar

from kalao.plc import core
from kalao.interface import status
from kalao.utils import database

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
# Read config file
parser = ConfigParser()
parser.read(config_path)

ADC1_MAX_ANGLE = parser.getfloat('PLC', 'ADC1_MAX_ANGLE')
ADC2_MAX_ANGLE = parser.getfloat('PLC', 'ADC2_MAX_ANGLE')
ADCAngleThreshold = parser.getfloat('PLC', 'ADCAngleThreshold')

adc_name = {1: 'ADC1_Newport_PR50PP.motor', 2: 'ADC2_Newport_PR50PP.motor'}

dispersion_adc = {
        450e-9:
                Polynomial([4.689e-2, 1.444e-5, -2.170e-6, 3.551e-9]) * 20 /
                1200 * 3600,  # ADC design start
        475e-9:
                Polynomial([3.795e-2, 1.169e-5, -1.756e-6, 2.874e-9]) * 20 /
                1200 * 3600,  # Sloan g'
        622e-9:
                Polynomial([8.897e-3, 2.739e-6, -4.117e-7, 6.738e-10]) * 20 /
                1200 * 3600,  # Sloan r'
        763e-9:
                Polynomial([-3.217e-3, -9.905e-7, 1.489e-7, -2.437e-10]) * 20 /
                1200 * 3600,  # Sloan i'
        905e-9:
                Polynomial([-1.013e-2, -3.119e-6, 4.689e-7, -7.675e-10]) * 20 /
                1200 * 3600,  # Sloan z'
        1018e-9:
                Polynomial([-1.375e-2, -4.233e-6, 6.364e-7, -1.042e-9]) * 20 /
                1200 * 3600,  # ADC design end
}

filter_to_wavelength = {
        'g': 475e-9,
        'r': 622e-9,
        'i': 763e-9,
        'z': 905e-9,
        'clear': [450e-9, 1018e-9],
        'nd': [450e-9, 1018e-9],
}

# Temperature in K
# Pressure in Pa
# Hygrometry between 0 and 1


# Owens 1967 formula
def air_refractive_index_OWENS(lambda0_, T, P, H):
    sig = 1. / (lambda0_ * 1e6)
    P = P / 100
    t = T - 273.15

    Pw_sat = 6.11 * 10**((7.5 * t) / (t + 237.7))
    Pw = Pw_sat * H
    Ps = P - Pw

    Ds = Ps / T * (1 + Ps * (57.90e-8 - 9.3250e-4 / T + 0.25844 / T**2))
    Dw = Pw / T * (
            1 + Pw * (1 + 3.70e-4 * Pw) *
            (-2.37321e-3 + 2.23366 / T - 710.792 / T**2 + 7.75141e4 / T**3))

    n = (2371.34 + 683939.7 / (130. - sig**2) + 4547.3 /
         (38.9 - sig**2)) * Ds + (6487.31 + 58.058 * sig**2 -
                                  0.71150 * sig**4 + 0.08851 * sig**6) * Dw

    return 1 + n * 1e-8


# Edlen 1966 formula
def air_refractive_index_EDLEN(lambda0_, T, P, H=None):
    sig = 1. / (lambda0_ * 1e6)
    p = P / 101325 * 760
    t = T - 273.15

    n = 8342.13 + 2406030 / (130. - sig**2) + 15997. / (38.9 - sig**2)
    n *= 0.00138823 * p / (1 + 0.003671 * t)

    return 1 + n * 1e-8


def dispersion_air(alt, wavelength, T, P, H=0):
    wavelength_ref = 715e-9
    air_refractive_index = air_refractive_index_EDLEN

    zenith_angle = (90 - alt) * np.pi / 180

    return np.tan(zenith_angle) * (
            air_refractive_index(wavelength, T, P, H) -
            air_refractive_index(wavelength_ref, T, P, H)) * 180 / np.pi * 3600


def get_optimal_adc_angle(alt, wavelength, T, P):
    # Check the dispersion of the ADC is big enough for small elevations
    target_dispersion = dispersion_air(alt, wavelength, T, P)
    dispersion = dispersion_adc[wavelength]

    res = minimize_scalar(lambda x: np.abs(dispersion(x) - target_dispersion),
                          bounds=(0, 180))

    if res.success and res.fun < 1e-2:
        return res.x
    else:
        return 0


def config_adc(beck=None, override_threshold=False):
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    filter_name = status.filter_name()
    T = status.outside_temperature()
    P = status.outside_pressure()
    alt = status.telescope_coord_altaz().alt.degrees

    wavelength = filter_to_wavelength[filter_name]

    # TODO: in case if filter_name is not in filter_to_wavelength

    if type(wavelength) == list:
        angle = 0

        for w in wavelength:
            angle += get_optimal_adc_angle(alt, w, T, P)

        angle /= len(wavelength)
    else:
        angle = get_optimal_adc_angle(alt, wavelength, T, P)

    current_angle = status.adc_angle()

    if override_threshold or np.abs(angle - current_angle) > ADCAngleThreshold:
        set_angle(angle, beck=beck)

    if disconnect_on_exit:
        beck.disconnect()

    return 0


def set_max_disp(beck=None):

    beck, disconnect_on_exit = core.check_beck(beck)

    set_angle(0, beck=beck)

    if disconnect_on_exit:
        beck.disconnect()

    return 0


def set_zero_disp(beck=None):
    beck, disconnect_on_exit = core.check_beck(beck)

    set_angle(180, beck=beck)

    if disconnect_on_exit:
        beck.disconnect()

    return 0


def set_angle(angle, beck=None):
    # Motors are face to face, offset by same angle so they are counter-rotating
    rotate(1, position=ADC1_MAX_ANGLE + angle / 2, beck=beck)
    rotate(2, position=ADC2_MAX_ANGLE + angle / 2, beck=beck)

    # TODO: check motors moved successfully
    database.store_obs_log({'adc_angle': angle})


def _set_value(adc_id, value_path, value, beck=None):
    beck, disconnect_on_exit = core.check_beck(beck)

    value_node = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + "." +
                               value_path)
    value_node.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(float(value),
                               value_node.get_data_type_as_variant_type())))

    sleep(0.1)
    new_value = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + "." +
                              value_path).get_value()
    if disconnect_on_exit:
        beck.disconnect()

    return new_value


def rotate(adc_id, position=0, beck=None):
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    # define commands
    motor_nCommand = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                   ".ctrl.nCommand")
    motor_bExecute = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                   ".ctrl.bExecute")

    # Check if initialised
    init_result = initialise(adc_id, force_init=False, beck=beck,
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
                    ua.Variant(
                            float(1),
                            motor_lrVelocity.get_data_type_as_variant_type())))
    motor_lrPosition = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                     ".ctrl.lrPosition")

    if isinstance(position, numbers.Number):
        # Set target position
        motor_lrPosition.set_attribute(
                ua.AttributeIds.Value,
                ua.DataValue(
                        ua.Variant(
                                float(position),
                                motor_lrPosition.get_data_type_as_variant_type(
                                ))))
        # Set move command
        motor_nCommand.set_attribute(
                ua.AttributeIds.Value,
                ua.DataValue(
                        ua.Variant(
                                int(3),
                                motor_nCommand.get_data_type_as_variant_type())
                ))
        # Execute
        send_execute(motor_bExecute)
        while beck.get_node(
                "ns=4; s=MAIN." + adc_name[adc_id] +
                ".stat.sStatus").get_value() == 'MOVING in Positioning Mode':
            print('.')
            sleep(5)
        # Get new position
        new_position = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                     ".stat.lrPosActual").get_value()
        # motor_lrPosition = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".ctrl.lrPosition")
    else:
        print('Expected position to be a number, received: ' + str(position))
        new_position = -1

    if disconnect_on_exit:
        beck.disconnect()

    return new_position


def status(adc_id, beck=None):
    """
    Query the status of the ADC motor.

    :return: complete status of calibration unit
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    status_dict = core.device_status(adc_name[adc_id], beck=beck)
    # status_dict = {'sStatus': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.sStatus").get_value(),
    #                'sErrorText': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.sErrorText").get_value(),
    #                'nErrorCode': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.nErrorCode").get_value(),
    #                'lrVelActual': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.lrVelActual").get_value(),
    #                'lrVelTarget': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.lrVelTarget").get_value(),
    #                'lrPosActual': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.lrPosActual").get_value(),
    #                'lrPosition': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".ctrl.lrPosition").get_value()}

    if disconnect_on_exit:
        beck.disconnect()

    return status_dict


def check_error(adc_id, beck=None):
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    if beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                     ".stat.sErrorText").get_value() == 0:
        adc_status = 0
    else:
        adc_status = 'ERROR'

    if disconnect_on_exit:
        beck.disconnect()

    return adc_status


def initialise(adc_id, force_init=False, beck=None, motor_nCommand=None,
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
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

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
                        ua.Variant(
                                True,
                                motor_bEnable.get_data_type_as_variant_type()))
        )
        if not beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                             ".stat.bEnabled").get_value():
            error = 'ERROR: ' + str(
                    beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                  ".stat.nErrorCode").get_value())
            init_status = error

    # Check if init, if not do init
    if not beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                         ".stat.bInitialised").get_value() or force_init:
        send_init(motor_nCommand, motor_bExecute)
        print('Initalising ADC motor' + str(adc_id))
        sleep(15)
        while beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                            ".stat.sStatus").get_value() == 'INITIALISING':
            print('.')
            sleep(15)
        if not beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                             ".stat.bInitialised").get_value():
            error = 'ERROR: ' + str(
                    beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                  ".stat.nErrorCode").get_value())
            init_status = error

    if disconnect_on_exit:
        beck.disconnect()

    return init_status


def send_execute(motor_bExecute):
    motor_bExecute.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            True,
                            motor_bExecute.get_data_type_as_variant_type())))


def send_init(motor_nCommand, motor_bExecute):
    motor_nCommand.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            int(1),
                            motor_nCommand.get_data_type_as_variant_type())))
    # Execute
    send_execute(motor_bExecute)
