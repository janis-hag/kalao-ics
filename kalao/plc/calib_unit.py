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

import numbers
from time import sleep

import numpy as np

import kalao.plc.core
from kalao.plc import core
from kalao.utils import database

from opcua import ua

import config

# TODO store errors in obs


def move_to_tungsten_position():
    """
    Move calibration unit to the position where the tungsten lamp is

    :return: position of the calibration unit
    """

    new_position = move(position=config.Tungsten.position)

    if np.around(new_position,
                 decimals=1) == np.around(config.Tungsten.position,
                                          decimals=1):
        ret = new_position
    else:
        database.store(
            'obs', {
                'calib_unit_log':
                    f'[ERROR] Calib unit position requested {config.Tungsten.position} but moved to {new_position}'
            })
        ret = -1

    return ret


def move_to_laser_position():
    """
    Move calibration unit to the position where the laser lamp is

    :return: position of the calibration unit
    """

    new_position = move(position=config.Laser.position)

    if np.around(new_position,
                 decimals=1) == np.around(config.Laser.position, decimals=1):
        ret = new_position
    else:
        database.store(
            'obs', {
                'calib_unit_log':
                    f'[ERROR] Calib unit position requested {config.Laser.position} but moved to {new_position}'
            })
        ret = -1

    return ret


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
        return -1

    current_position = plc_status()['lrPosActual']

    if absolute:
        position = config.CalibUnit.initial_offset + config.CalibUnit.px_to_mm * pixel
    else:
        position = current_position + config.CalibUnit.px_to_mm * pixel

    new_position = move(position)

    return new_position


@core.beckhoff_autoconnect
def move(position=23.36, velocity=0.1, beck=None):
    """
    Move the calibration unit to position

    :param position: position to move to
    :param beck: handle to the beckhoff connection if it's already open
    :return: position the calib unit has been moved to
    """

    database.store('obs', {
        'calib_unit_log': f'Moving calibration unit to position: {position}mm'
    })

    # define commands
    motor_nCommand = beck.get_node(
        "ns=4; s=MAIN.Linear_Standa_8MT.ctrl.nCommand")

    # Check if initialised
    init_result = init(force_init=False, beck=beck,
                       motor_nCommand=motor_nCommand)
    if not init_result == 0:
        return init_result

    # Set velocity
    motor_lrVelocity = beck.get_node(
        "ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrVelocity")
    motor_lrVelocity.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(float(velocity),
                       motor_lrVelocity.get_data_type_as_variant_type())))
    motor_lrPosition = beck.get_node(
        "ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrPosition")

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
        send_execute(beck)

        sleep(2)
        wait_move(beck=beck)

        # Get new position
        new_position = beck.get_node(
            "ns=4; s=MAIN.Linear_Standa_8MT.stat.lrPosActual").get_value()
        # motor_lrPosition = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrPosition")

        database.store(
            'obs', {
                'calib_unit_log':
                    f'Moved calibration unit to position: {new_position}'
            })
    else:
        database.store(
            'obs', {
                'calib_unit_log':
                    f'Expected position to be a number, received: {position}'
            })
        new_position = -1

    return new_position


@core.beckhoff_autoconnect
def wait_move(beck=None):
    core.wait_loop(
        f'Waiting for calibration unit movement',
        lambda: beck.get_node(f"ns=4; s=MAIN.Linear_Standa_8MT.stat.sStatus"
                              ).get_value().startswith('MOVING'), 5)

    return 0


def plc_status(beck=None):
    """
    Query the status of the calibration unit.

    :return: complete status of calibration unit
    """

    return kalao.plc.core.device_status('Linear_Standa_8MT', beck=beck)


def get_position(beck=None):

    return plc_status()['lrPosActual']


def check_error(beck):
    """
    Check the status of the calibration unit motor for errors.

    :param beck: the handle for the plc connection
    :return:
    """

    error_text = beck.get_node(
        "ns=4; s=MAIN.Linear_Standa_8MT.stat.sErrorText").get_value()

    if error_text == 0:
        return 0
    else:
        database.store('obs', {'calib_unit_log': f'[ERROR] {error_text}'})
        return -1


@core.beckhoff_autoconnect
def init(force_init=True, beck=None, motor_nCommand=None):
    '''
    Initialise the calibration unit.

    :param beck: the handle for the plc connection
    :param motor_nCommand: handle to send commands to the motor
    :return: returns 0 on success and error code on failure
    '''

    database.store('obs', {'calib_unit_log': 'Initialising calibration unit'})

    if motor_nCommand is None:
        # define commands
        motor_nCommand = beck.get_node(
            "ns=4; s=MAIN.Linear_Standa_8MT.ctrl.nCommand")

    # Set reset on error to true in case it has been changed
    #motor_bResetError = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bResetError")
    #motor_bResetError.set_attribute(ua.AttributeIds.Value,
    #                               ua.DataValue(ua.Variant(True, motor_bResetError.get_data_type_as_variant_type())))

    # Check if enabled, if no do enable
    if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bEnabled"
                         ).get_value() or force_init:
        motor_bEnable = beck.get_node(
            "ns = 4; s = MAIN.Linear_Standa_8MT.ctrl.bEnable")
        motor_bEnable.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                ua.Variant(True,
                           motor_bEnable.get_data_type_as_variant_type())))
        if not beck.get_node(
                "ns=4; s=MAIN.Linear_Standa_8MT.stat.bEnabled").get_value():
            error = '[ERROR] ' + str(
                beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.nErrorCode"
                              ).get_value())

            return error

    # Check if init, if not do init
    if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bInitialised"
                         ).get_value() or force_init:
        send_init(beck, motor_nCommand)
        database.store('obs',
                       {'calib_unit_log': f'Starting calibration unit init.'})

        sleep(15)

        core.wait_loop(
            f'Waiting for calibration unit initialisation', lambda: beck.
            get_node(f"ns=4; s=MAIN.Linear_Standa_8MT.stat.sStatus").get_value(
            ).startswith('INITIALISING'), 5)

        if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bInitialised"
                             ).get_value():
            error = '[ERROR] ' + str(
                beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.nErrorCode"
                              ).get_value())

            return error

    return 0


def send_execute(beck):
    motor_bExecute = beck.get_node(
        "ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bExecute")

    motor_bExecute.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, motor_bExecute.get_data_type_as_variant_type())))


def send_init(beck, motor_nCommand):
    motor_nCommand.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(int(1),
                       motor_nCommand.get_data_type_as_variant_type())))
    # Execute
    send_execute(beck)
