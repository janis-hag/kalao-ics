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

node_path = 'Tungsten'

def check_error(beck):
    if beck.get_node("ns=4; s=MAIN.Tungsten.stat.sErrorText").get_value() == 0:
        return 0
    else:
        error_status = 'ERROR'
        return error_status


def on(beck=None):
    '''
    Turn off tungsten lamp

    :param beck: handle to for the beckhoff connection
    :return: status of the lamp
    '''

    state = send_command(beck, 3)
    return state


def off(beck=None):
    '''
    Turn off tungsten lamp

    :param beck: handle to for the beckhoff connection
    :return: status of the lamp
    '''

    state = send_command(beck, 2)
    return state


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
                                    ua.DataValue(ua.Variant(int(nCommand_value),
                                                            tungsten_nCommand.get_data_type_as_variant_type())))
    # Execute
    send_execute(beck)

    state = beck.get_node("ns=4; s=MAIN.Tungsten.stat.nStatus").get_value()

    return state



def initialise(beck=None, tungsten_nCommand=None):
    '''
    Initialise the calibration unit.

    :param beck: the handle for the plc connection
    :param tungsten_nCommand: handle to send commands to the motor
    :return: returns 0 on success and error code on failure
    '''
    if beck is None:
        # Connect to OPCUA server
        disconnect_on_exit = True
        beck = core.connect()
    else:
        disconnect_on_exit = False
    # if tungsten_nCommand is None:
    #     # define commands
    tungsten_status = 'ERROR'

    # Check if init, if not do init
    if not beck.get_node("ns=4; s=MAIN.Tungsten.stat.bInitialised").get_value():
        # init
        send_command(beck, 1)
        sleep(15)
        while(beck.get_node("ns=4; s=MAIN.Tungsten.stat.sStatus").get_value() == 'INITIALISING'):
            sleep(15)
        if not beck.get_node("ns=4; s=MAIN.Tungsten.stat.bInitialised").get_value():
            tungsten_status = 'ERROR: '+str(beck.get_node("ns=4; s=MAIN.Tungsten.stat.nErrorCode").get_value())
        else:
            tungsten_status = beck.get_node("ns=4; s=MAIN.Tungsten.stat.sStatus").get_value()
    else:
        tungsten_status = 0

    if disconnect_on_exit:
        beck.disconnect()

    return tungsten_status


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

    node_path = 'Tungsten'

    # Connect to OPCUA server
    if beck is None:
        disconnect_on_exit = True
        beck = core.connect()
    else:
        disconnect_on_exit = False

    device_status_dict = {'sStatus': beck.get_node("ns=4; s=MAIN." + node_path + ".stat.sStatus").get_value(),
                          'sErrorText': beck.get_node("ns=4; s=MAIN." + node_path + ".stat.sErrorText").get_value(),
                          'nErrorCode': beck.get_node("ns=4; s=MAIN." + node_path + ".stat.nErrorCode").get_value(),
                          'nStatus': beck.get_node("ns=4; s=MAIN." + node_path + ".stat.nStatus").get_value()}

    if disconnect_on_exit:
        beck.disconnect()

    return device_status_dict


def switch(action_name):
    """
     Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
    :return: position of flipmirror
    """
    # Connect to OPCUA server
    beck = core.connect()

    tungsten_switch = beck.get_node("ns = 4; s = MAIN.Tungsten." + action_name)
    tungsten_switch.set_attribute(
        ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, tungsten_switch.get_data_type_as_variant_type())))

    sleep(1)
    tungsten_status = beck.get_node("ns=4; s=MAIN." + node_path + ".stat.sStatus").get_value()
    beck.disconnect()

    return tungsten_status

