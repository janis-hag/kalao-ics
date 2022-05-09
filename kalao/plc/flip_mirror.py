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

from kalao.utils import database
from kalao.plc import core

from opcua import ua
from time import sleep


def status(beck=None):
    """
    Query the status of the flip mirror.

    :return: complete status of flip mirror
    """

    status_dict = core.device_status('Flip.FlipMirror', beck=beck)

    return status_dict


def down(beck=None):
    """
    Move the flip mirror down

    :return: status of the flip_mirror
    """
    flip_position = switch('bDown_Flip', beck=beck)
    return flip_position


def up(beck=None):
    """
    Move the flip mirror up

    :return: status of the flip_mirror
    """
    flip_position = switch('bUp_Flip', beck=beck)
    return flip_position


def switch(action_name, beck=None):
    """
     Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
    :return: position of flip_mirror
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    shutter_switch = beck.get_node("ns = 4; s = MAIN.Flip." + action_name)
    shutter_switch.set_attribute(
        ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, shutter_switch.get_data_type_as_variant_type())))

    sleep(1)
    if beck.get_node("ns=4;s=MAIN.Flip.bStatus_Up_Flip").get_value():
        flip_position = 'UP'
    elif beck.get_node("ns=4;s=MAIN.Flip.bStatus_Down_Flip").get_value():
        flip_position = 'DOWN'
    else:
        flip_position = 'ERROR'

    if disconnect_on_exit:
        beck.disconnect()

    return flip_position


def position(beck=None):
    """
    Query the single string status of the shutter.

    :return: single string status of shutter
    """
    if 'flip_mirror' in core.disabled_device_list():
        return 1

    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    # TODO check if initialised and not disabled

    # Check error status
    error_code = beck.get_node('ns=4;s=MAIN.Flip.FlipMirror.stat.nErrorCode').get_value()
    if error_code != 0:
        #someting went wrong
        # Logging error
        error_text = beck.get_node("ns=4; s=MAIN.Flip.FlipMirror.stat.sErrorText").get_value()
        database.store_obs_log({'flip_mirror_log': 'ERROR' + str(error_code) + ': '+error_text})
        flip_position = error_text

    else:
        if beck.get_node("ns=4;s=MAIN.Flip.bStatus_Up_Flip").get_value():
            flip_position = 'UP'
        elif beck.get_node("ns=4;s=MAIN.Flip.bStatus_Down_Flip").get_value():
            flip_position = 'DOWN'
        else:
            flip_position = 'ERROR'

    if disconnect_on_exit:
        beck.disconnect()

    return flip_position


def initialise(beck=None):

    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    down(beck)
    sleep(1)
    up(beck=beck)
    sleep(1)
    down(beck=beck)

    if disconnect_on_exit:
        beck.disconnect()

    return 0
