#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : tungsten
# @Date : 2021-01-27-14-21
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
tungsten.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""


from . import core
from opcua import ua
from time import sleep


def check_error(beck):
    if beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sErrorText").get_value() == 0:
        return 0
    else:
        error_status = 'ERROR'
        return


def initialise(beck=None, motor_nCommand=None):
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

    # Check if enabled, if no do enable
    if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bEnabled").get_value():
        motor_bEnable = beck.get_node("ns = 4; s = MAIN.Linear_Standa_8MT.ctrl.bEnable")
        motor_bEnable.set_attribute(
            ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, motor_bEnable.get_data_type_as_variant_type())))
        if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bEnabled").get_value():
            error = 'ERROR: '+str(beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.nErrorCode").get_value())
            return error

    # Check if init, if not do init
    if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bInitialised").get_value():
        send_init(beck, motor_nCommand)
        sleep(15)
        while(beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sStatus").get_value() == 'INITIALISING'):
            sleep(15)
        if not beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.bInitialised").get_value():
            error = 'ERROR: '+str(beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.nErrorCode").get_value())
            return error
    return 0


def switch(action_name):
    """
     Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
    :return: position of flipmirror
    """
    # Connect to OPCUA server
    beck = core.connect()

    laser_switch = beck.get_node("ns = 4; s = MAIN.Laser." + action_name)
    laser_switch.set_attribute(
        ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, laser_switch.get_data_type_as_variant_type())))

    sleep(1)
    if beck.get_node("ns=4;s=MAIN.Laser.bDisable").get_value():
        laser_status = 'OFF'
    else:
        laser_status = 'ON'

    beck.disconnect()
    return laser_status


def send_command(beck, motor_nCommand):
    motor_nCommand.set_attribute(ua.AttributeIds.Value,
                                 ua.DataValue(ua.Variant(int(1), motor_nCommand.get_data_type_as_variant_type())))
    # Execute
    send_execute(beck)


def send_execute(beck):
    motor_bExecute = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bExecute")

    motor_bExecute.set_attribute(
        ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, motor_bExecute.get_data_type_as_variant_type())))


def send_init(beck, motor_nCommand):
    motor_nCommand.set_attribute(ua.AttributeIds.Value,
                                 ua.DataValue(ua.Variant(int(1), motor_nCommand.get_data_type_as_variant_type())))
    # Execute
    send_execute(beck)

