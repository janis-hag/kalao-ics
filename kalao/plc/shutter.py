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

from kalao.plc import core
from opcua import ua
from time import sleep
from kalao.utils import database


def status(beck=None):
    """
    Query the status of the shutter

    :return: complete status of shutter
    """

    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    status_dict = core.device_status('Shutter.Shutter', beck=beck)

    if status_dict['sStatus'] == 'STANDING':
        status_dict['sStatus'] = position(beck=beck)

    if disconnect_on_exit:
        beck.disconnect()

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


def position(beck=None):
    """
    Query the single string status of the shutter.

    :return: single string status of shutter
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    # Check error status
    error_code = beck.get_node(
            "ns=4; s=MAIN.Shutter.Shutter.stat.nErrorCode").get_value()
    if error_code != 0:
        #someting went wrong
        error_text = beck.get_node(
                "ns=4; s=MAIN.Shutter.Shutter.stat.sErrorText").get_value()
        database.store_obs_log({
                'shutter_log':
                        'ERROR' + str(error_code) + ': ' + str(error_text)
        })

        position_status = error_text

    else:
        if beck.get_node(
                "ns=4; s=MAIN.Shutter.bStatus_Closed_Shutter").get_value():
            bStatus = 'CLOSED'
        else:
            bStatus = 'OPEN'

        position_status = bStatus

    if disconnect_on_exit:
        beck.disconnect()

    return position_status


def initialise(beck=None):
    """
    Initialise the shutter.

    :return: status of shutter
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    init_status = beck.get_node(
            "ns=4; s=MAIN.Shutter.Shutter.stat.nErrorCode").get_value()

    initial_position = position(beck=beck)

    # Do the shutter gym
    if initial_position == 'OPEN':
        shutter_close(beck)
        sleep(3)
        shutter_open(beck)
    elif initial_position == 'CLOSED':
        shutter_open(beck)
        sleep(3)
        shutter_close(beck)

    if disconnect_on_exit:
        beck.disconnect()

    return init_status


def shutter_open(beck=None):
    """
    Open the shutter.

    :return: status of shutter
    """
    database.store_obs_log({'shutter_log': 'Opening shutter'})
    bStatus = switch('bOpen_Shutter', beck=beck)

    return bStatus


def shutter_close(beck=None):
    """
    Close the shutter.

    :return: status of shutter
    """
    database.store_obs_log({'shutter_log': 'Closing shutter'})

    bStatus = switch('bClose_Shutter', beck=beck)

    return bStatus


def switch(action_name, beck=None):
    """
     Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
    :return: status of shutter
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    shutter_switch = beck.get_node("ns = 4; s = MAIN.Shutter." + action_name)
    shutter_switch.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            True,
                            shutter_switch.get_data_type_as_variant_type())))

    sleep(1)

    if beck.get_node(
            "ns=4; s=MAIN.Shutter.bStatus_Closed_Shutter").get_value():
        bStatus = 'CLOSED'
    else:
        bStatus = 'OPEN'

    if disconnect_on_exit:
        beck.disconnect()

    return bStatus
