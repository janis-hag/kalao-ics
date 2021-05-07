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

from . import core
import numbers
from opcua import Client, ua
from time import sleep


def move(position=23.36):

    # Connect to OPCUA server
    beck = core.connect()
    # define commands
    motor_nCommand = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.nCommand")

    # Check if initialised
    init_result = initialise(force_init=False, beck=beck, motor_nCommand=motor_nCommand)
    if not init_result == 0:
        return init_result

    # Set velocity to 1 in case is has been changed
    motor_lrVelocity = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrVelocity")
    motor_lrVelocity.set_attribute(ua.AttributeIds.Value,
                                   ua.DataValue(ua.Variant(float(1), motor_lrVelocity.get_data_type_as_variant_type())))
    motor_lrPosition = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrPosition")

    if isinstance(position, numbers.Number):
        # Set target position
        motor_lrPosition.set_attribute(
            ua.AttributeIds.Value, ua.DataValue(ua.Variant(float(position),
                                                           motor_lrPosition.get_data_type_as_variant_type())))
        # Set move command
        motor_nCommand.set_attribute(
            ua.AttributeIds.Value, ua.DataValue(ua.Variant(int(3),
                                                           motor_nCommand.get_data_type_as_variant_type())))
        # Execute
        send_execute(beck)
        # Get new position
        new_position = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrPosActual").get_value()
        # motor_lrPosition = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrPosition")
    else:
        print('Expected position to be a number, received: ' + str(position))
        new_position = -99

    # Disconnect from OPCUA server
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
    if beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sErrorText").get_value() == 0:
        return 0
    else:
        error_status = 'ERROR'
        return


def initialise(force_init=False, beck=None, motor_nCommand=None):
    '''
    Initialise the calibration unit.

    :param beck: the handle for the plc connection
    :param motor_nCommand: handle to send commands to the motor
    :return: returns 0 on success and error code on failure
    '''
    if beck is None:
        # Connect to OPCUA server
        beck = core.connect()
    if motor_nCommand is None:
        # define commands
        motor_nCommand = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.nCommand")

    # Set reset on error to true in case it has been changed
    motor_bResetError = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bResetError")
    motor_bResetError.set_attribute(ua.AttributeIds.Value,
                                    ua.DataValue(ua.Variant(True, motor_bResetError.get_data_type_as_variant_type())))

    # Check if enabled, if no do enable
    if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bEnabled").get_value() or force_init:
        motor_bEnable = beck.get_node("ns = 4; s = MAIN.Linear_Standa_8MT.ctrl.bEnable")
        motor_bEnable.set_attribute(
            ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, motor_bEnable.get_data_type_as_variant_type())))
        if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bEnabled").get_value():
            error = 'ERROR: '+str(beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.nErrorCode").get_value())
            return error

    # Check if init, if not do init
    if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bInitialised").get_value() or force_init:
        send_init(beck, motor_nCommand)
        print('Starting calib_unit init.')
        sleep(15)
        while(beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sStatus").get_value() == 'INITIALISING'):
            print('.')
            sleep(15)
        if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bInitialised").get_value():
            error = 'ERROR: '+str(beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.nErrorCode").get_value())
            return error
    return 0


def send_execute(beck):
    motor_bExecute = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bExecute")

    motor_bExecute.set_attribute(
        ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, motor_bExecute.get_data_type_as_variant_type())))


def send_init(beck, motor_nCommand):
    motor_nCommand.set_attribute(ua.AttributeIds.Value,
                                 ua.DataValue(ua.Variant(int(1), motor_nCommand.get_data_type_as_variant_type())))
    # Execute
    send_execute(beck)
