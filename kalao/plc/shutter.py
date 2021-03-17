#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : shutter.py
# @Date : 2021-01-02-15-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
shutter.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from . import core
from opcua import ua
from time import sleep


def status(beck=None):
    """
    Query the status of the shutter

    :return: complete status of shutter
    """

    status_dict = core.device_status('Shutter.Shutter', beck=beck)

    return status_dict


# def short_status():
#     """
#     Query the single string status of the shutter.
#
#     :return: single string status of shutter
#     """
#     # Connect to OPCUA server
#     beck = core.connect()
#
#     # Check error status
#     error_code = beck.get_node("ns=4; s=MAIN.Shutter.Shutter.stat.nErrorCode").get_value()
#     if error_code != 0:
#         #someting went wrong
#         return beck.get_node("ns=4; s=MAIN.Shutter.Shutter.stat.sStatus").get_value()
#
#     # beck.get_node("ns=4; s=MAIN.Shutter.stat.lrPosActual").get_value()
#     # beck.get_node("ns=4; s=MAIN.Shutter.stat.sStatus").get_value()
#     # beck.get_node("ns=4; s=MAIN.Shutter.stat.sErrorText").get_value()
#     # beck.get_node("ns=4; s=MAIN.Shutter.stat.lrVelActual").get_value()
#     # beck.get_node("ns=4; s=MAIN.Shutter.stat.lrVelTarget").get_value()
#
#     beck.disconnect()


def position():
    """
    Query the single string status of the shutter.

    :return: single string status of shutter
    """
    # Connect to OPCUA server
    beck = core.connect()

    # Check error status
    error_code = beck.get_node("ns=4; s=MAIN.Shutter.Shutter.stat.nErrorCode").get_value()
    if error_code != 0:
        #someting went wrong
        beck.disconnect()
        return beck.get_node("ns=4; s=MAIN.Shutter.Shutter.stat.sErrorText").get_value()
    else:
        if beck.get_node("ns=4; s=MAIN.Shutter.bStatus_Shutter").get_value():
            bStatus = 'CLOSE'
        else:
            bStatus = 'OPEN'
        beck.disconnect()
        return bStatus

def initialise():
    """
    Initialise the shutter.

    :return: status of shutter
    """
    # Connect to OPCUA server
    beck = core.connect()

    status = beck.get_node("ns=4; s=MAIN.Shutter.bStatus_Shutter").get_value()

    beck.disconnect()

    return status


def open():
    """
    Open the shutter.

    :return: status of shutter
    """
    bStatus = switch('bOpen_Shutter')
    return bStatus


def close():
    """
    Close the shutter.

    :return: status of shutter
    """
    bStatus = switch('bClose_Shutter')
    return bStatus


def switch(action_name):
    """
     Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
    :return: status of shutter
    """
    # Connect to OPCUA server
    beck = core.connect()

    shutter_switch = beck.get_node("ns = 4; s = MAIN.Shutter." + action_name)
    shutter_switch.set_attribute(
        ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, shutter_switch.get_data_type_as_variant_type())))

    sleep(1)

    if beck.get_node("ns=4; s=MAIN.Shutter.bStatus_Shutter").get_value():
        bStatus = 'CLOSE'
    else:
        bStatus = 'OPEN'

    beck.disconnect()
    return bStatus
