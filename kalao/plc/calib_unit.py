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

from kalao.plc import core
from kalao.utils import database
from sequencer import system

import numbers
from opcua import ua
from time import sleep
from configparser import ConfigParser
from pathlib import Path
import os

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
# Read config file
parser = ConfigParser()
parser.read(config_path)

LASER_POSITION = parser.getfloat('PLC', 'LaserPosition')
TUNGSTEN_POSITION = parser.getfloat('PLC', 'TungstenPosition')
Pixel2mm = parser.getfloat('PLC', 'CalibUnitPixel2mm')
mmOffset = parser.getfloat('PLC', 'CalibUnitmmOffset')
# TODO store errors in obs_log


def _update_db(beck=None):
    """
    Update the database with the current calib_unit position

    :param beck: handle to the beckhoff connection if it's already open
    :return:
    """

    database.store_monitoring({'calib_unit': status(beck=beck)['lrPosActual']})


def _log(message):
    """
    Print and log to obs_log messages concerning the calibration unit

    :param message: message to print and log
    :return:
    """

    print('Calib unit: ' + str(message))
    database.store_obs_log({'calib_unit_log': message})


def tungsten_position():
    """
    Move calibration unit to the position where the tungsten lamp is

    :return: position of the calibration unit
    """

    new_position = move(position=TUNGSTEN_POSITION)
    return new_position


def laser_position():
    """
    Move calibration unit to the position where the laser lamp is

    :return: position of the calibration unit
    """

    new_position = move(position=LASER_POSITION)
    return new_position


def pixel_move(pixel, absolute=False):
    """
    Move calib unit by amount of pixels

    :param pixel: pixel to move to
    :return:
    """

    if absolute and pixel < 0:
        system.print_and_log(
                'ERROR: Calib unit absolute value should not be negative')
        return -1

    current_position = status()['lrPosActual']

    if absolute:
        position = mmOffset + Pixel2mm * pixel
    else:
        position = current_position + Pixel2mm * pixel

    new_position = move(position)

    return new_position


def move(position=23.36, beck=None):
    """
    Move the calibration unit to position

    :param position: position to move to
    :param beck: handle to the beckhoff connection if it's already open
    :return: position the calib unit has been moved to
    """

    _log(f'Moving to position: {position}')

    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    # define commands
    motor_nCommand = beck.get_node(
            "ns=4; s=MAIN.Linear_Standa_8MT.ctrl.nCommand")

    # Check if initialised
    init_result = initialise(force_init=False, beck=beck,
                             motor_nCommand=motor_nCommand)
    if not init_result == 0:
        return init_result

    # Set velocity to 1 in case is has been changed
    motor_lrVelocity = beck.get_node(
            "ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrVelocity")
    motor_lrVelocity.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            float(0.5),
                            motor_lrVelocity.get_data_type_as_variant_type())))
    motor_lrPosition = beck.get_node(
            "ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrPosition")

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
        send_execute(beck)
        while (beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sStatus").
               get_value() == 'MOVING in Positioning Mode'):
            print('.')
            sleep(5)
        # Get new position
        new_position = beck.get_node(
                "ns=4; s=MAIN.Linear_Standa_8MT.stat.lrPosActual").get_value()
        # motor_lrPosition = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrPosition")
    else:
        print('Expected position to be a number, received: ' + str(position))
        new_position = -99

    _log(f'Moved to position: {new_position}')

    # Disconnect from OPCUA server
    if disconnect_on_exit:
        beck.disconnect()

    return new_position


def status(beck=None):
    """
    Query the status of the calibration unit.

    :return: complete status of calibration unit
    """
    # # Connect to OPCUA server
    # if beck is None:
    #     disconnect_on_exit = True
    #     beck = core.connect()
    # else:
    #     disconnect_on_exit = False

    status_dict = core.device_status('Linear_Standa_8MT', beck=beck)
    # status_dict = {'sStatus': beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sStatus").get_value(),
    #                'sErrorText': beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sErrorText").get_value(),
    #                'nErrorCode': beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.nErrorCode").get_value(),
    #                'lrVelActual': beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrVelActual").get_value(),
    #                'lrVelTarget': beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrVelTarget").get_value(),
    #                'lrPosActual': beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrPosActual").get_value(),
    #                'lrPosition': beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrPosition").get_value()}

    # if disconnect_on_exit:
    #     beck.disconnect()

    return status_dict


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
        _log(f'ERROR: {error_text}')
        return -1


def initialise(force_init=True, beck=None, motor_nCommand=None):
    '''
    Initialise the calibration unit.

    :param beck: the handle for the plc connection
    :param motor_nCommand: handle to send commands to the motor
    :return: returns 0 on success and error code on failure
    '''
    #if beck is None:
    #    # Connect to OPCUA server
    #    beck = core.connect()

    beck, disconnect_on_exit = core.check_beck(beck)

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
                        ua.Variant(
                                True,
                                motor_bEnable.get_data_type_as_variant_type()))
        )
        if not beck.get_node(
                "ns=4; s=MAIN.Linear_Standa_8MT.stat.bEnabled").get_value():
            error = 'ERROR: ' + str(
                    beck.get_node(
                            "ns=4; s=MAIN.Linear_Standa_8MT.stat.nErrorCode").
                    get_value())

            if disconnect_on_exit:
                beck.disconnect()

            return error

    # Check if init, if not do init
    if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bInitialised"
                         ).get_value() or force_init:
        send_init(beck, motor_nCommand)
        _log(f'Starting calib_unit init.')
        sleep(15)
        while (beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sStatus").
               get_value() == 'INITIALISING'):
            print('.')
            sleep(15)
        if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bInitialised"
                             ).get_value():
            error = 'ERROR: ' + str(
                    beck.get_node(
                            "ns=4; s=MAIN.Linear_Standa_8MT.stat.nErrorCode").
                    get_value())

            if disconnect_on_exit:
                beck.disconnect()

            return error

    if disconnect_on_exit:
        beck.disconnect()

    return 0


def send_execute(beck):
    motor_bExecute = beck.get_node(
            "ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bExecute")

    motor_bExecute.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            True,
                            motor_bExecute.get_data_type_as_variant_type())))


def send_init(beck, motor_nCommand):
    motor_nCommand.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            int(1),
                            motor_nCommand.get_data_type_as_variant_type())))
    # Execute
    send_execute(beck)
