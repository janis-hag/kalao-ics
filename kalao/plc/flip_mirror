#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : flip_mirror
# @Date : 2021-01-02-15-08
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
flip_mirror.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from . import core
from opcua import ua
from time import sleep


def status(beck=None):
    """
    Query the status of the flip mirror.

    :return: complete status of flip mirror
    """

    status_dict = core.device_status('Flip.flip_mirror', beck=beck)

    return status_dict

def down():
    """
    Move the flip mirror down

    :return: status of the flip_mirror
    """
    flip_position = switch('bDown_Flip')
    return flip_position


def up():
    """
    Move the flip mirror up

    :return: status of the flip_mirror
    """
    flip_position = switch('bUp_Flip')
    return flip_position


def switch(action_name):
    """
     Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
    :return: position of flip_mirror
    """
    # Connect to OPCUA server
    beck = core.connect()

    shutter_switch = beck.get_node("ns = 4; s = MAIN.Flip." + action_name)
    shutter_switch.set_attribute(
        ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, shutter_switch.get_data_type_as_variant_type())))

    sleep(1)
    if beck.get_node("ns=4;s=MAIN.Flip.bStatus_Flip").get_value():
        flip_position = 'UP'
    else:
        flip_position = 'DOWN'

    beck.disconnect()
    return flip_position


def position():
    """
    Query the single string status of the shutter.

    :return: single string status of shutter
    """
    # Connect to OPCUA server
    beck = core.connect()

    # Check error status
    error_code = beck.get_node('ns=4;s=MAIN.Flip.flip_mirror.stat.nErrorCode').get_value()
    if error_code != 0:
        #someting went wrong
        beck.disconnect()
        return beck.get_node("ns=4; s=MAIN.Flip.flip_mirror.stat.sErrorText").get_value()
    else:
        if beck.get_node("ns=4;s=MAIN.Flip.bStatus_Flip").get_value():
            flip_position = 'UP'
        else:
            flip_position = 'DOWN'
        beck.disconnect()
        return flip_position