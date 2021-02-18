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
    if beck.get_node("ns=4; s=MAIN.Tungsten.stat.sErrorText").get_value() == 0:
        return 0
    else:
        error_status = 'ERROR'
        return


def initialise(beck=None, tungsten_nCommand=None):
    '''
    Initialise the calibration unit.

    :param beck: the handle for the plc connection
    :param tungsten_nCommand: handle to send commands to the motor
    :return: returns 0 on success and error code on failure
    '''
    if beck is None:
        # Connect to OPCUA server
        beck = core.connect()
    # if tungsten_nCommand is None:
    #     # define commands

    # Check if enabled, if no do enable
    if not beck.get_node("ns=4; s=MAIN.Tungsten.stat.bEnabled").get_value():
        send_enable(beck)

    # Check if init, if not do init
    if not beck.get_node("ns=4; s=MAIN.Tungsten.stat.bInitialised").get_value():
        # init
        send_command(beck, 1)
        sleep(15)
        while(beck.get_node("ns=4; s=MAIN.Tungsten.stat.sStatus").get_value() == 'INITIALISING'):
            sleep(15)
        if not beck.get_node("ns=4; s=MAIN.Tungsten.stat.bInitialised").get_value():
            error = 'ERROR: '+str(beck.get_node("ns=4; s=MAIN.Tungsten.stat.nErrorCode").get_value())
            return error
    return 0


def send_enable(beck):
    """
    Enable tungsten lamp
    :param beck: the handle for the plc connection
    :return:
    """
    tungsten_bEnable = beck.get_node("ns = 4; s = MAIN.Tungsten.ctrl.bEnable")
    tungsten_bEnable.set_attribute(
        ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, tungsten_bEnable.get_data_type_as_variant_type())))
    sleep(5)
    if not beck.get_node("ns=4; s=MAIN.Tungsten.stat.bEnabled").get_value():
        error = 'ERROR: '+str(beck.get_node("ns=4; s=MAIN.Tungsten.stat.nErrorCode").get_value())
        return error


def send_command(beck, nCommand_value):
    """
    Send a command to the tungsten lamp

    tungsten number commands are
    1 = init
    2 = OFF
    3 = ON

    :param beck: handle to the beckhoff connection
    :param nCommand_value: 1, 2, or 3
    :return:
    """

    tungsten_nCommand = beck.get_node("ns=4; s=MAIN.Tungsten.ctrl.nCommand")

    tungsten_nCommand.set_attribute(ua.AttributeIds.Value,
                                 ua.DataValue(ua.Variant(int(nCommand_value), tungsten_nCommand.get_data_type_as_variant_type())))
    # Execute
    send_execute(beck)


def send_execute(beck):
    tungsten_bExecute = beck.get_node("ns=4; s=MAIN.Tungsten.ctrl.bExecute")

    tungsten_bExecute.set_attribute(
        ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, tungsten_bExecute.get_data_type_as_variant_type())))


# def send_init(beck, tungsten_nCommand):
#     tungsten_nCommand.set_attribute(ua.AttributeIds.Value,
#                                  ua.DataValue(ua.Variant(int(1), tungsten_nCommand.get_data_type_as_variant_type())))
#     # Execute
#     send_execute(beck)


def status(beck=None):
    """
    Query the status of the tungsten lamp.

    :return: complete status of tungsten lamp
    """

    status_dict = core.device_status('Tungsten', beck=beck)

    return status_dict


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
