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

from time import sleep

import kalao.plc.core
from kalao.plc import core
from kalao.utils import database

from opcua import ua

from kalao.definitions.enums import FlipMirrorPosition


def plc_status(beck=None):
    """
    Query the status of the flip mirror.

    :return: complete status of flip mirror
    """

    return kalao.plc.core.device_status('Flip.FlipMirror', beck=beck)


def down(beck=None):
    """
    Move the flip mirror down

    :return: status of the flip_mirror
    """

    return _switch('bDown_Flip', beck=beck)


def up(beck=None):
    """
    Move the flip mirror up

    :return: status of the flip_mirror
    """

    return _switch('bUp_Flip', beck=beck)


@core.beckhoff_autoconnect
def _switch(action_name, beck=None):
    """
     Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
    :return: position of flip_mirror
    """

    if action_name == 'bUp_Flip':
        database.store('obs', {'flip_mirror_log': 'Flipping mirror up'})
    elif action_name == 'bDown_Flip':
        database.store('obs', {'flip_mirror_log': 'Flipping mirror down'})

    shutter_switch = beck.get_node("ns = 4; s = MAIN.Flip." + action_name)
    shutter_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, shutter_switch.get_data_type_as_variant_type())))

    sleep(1)

    position = get_position(beck)

    return position


@core.beckhoff_autoconnect
def get_position(beck=None):
    """
    Query the single string status of the shutter.

    :return: single string status of shutter
    """

    # Check error status
    error_code = beck.get_node(
        'ns=4;s=MAIN.Flip.FlipMirror.stat.nErrorCode').get_value()

    if error_code != 0:
        error_text = beck.get_node(
            "ns=4; s=MAIN.Flip.FlipMirror.stat.sErrorText").get_value()

        database.store('obs', {
            'flip_mirror_log': f'[ERROR] {error_text} ({error_code})'
        })

        position = FlipMirrorPosition.ERROR

    else:
        if beck.get_node("ns=4;s=MAIN.Flip.bStatus_Up_Flip").get_value():
            position = FlipMirrorPosition.UP
        elif beck.get_node("ns=4;s=MAIN.Flip.bStatus_Down_Flip").get_value():
            position = FlipMirrorPosition.DOWN
        else:
            position = FlipMirrorPosition.ERROR

    return position


@core.beckhoff_autoconnect
def init(beck=None):
    database.store('obs', {'flip_mirror_log': 'Initialising flip mirror'})

    # Do the flip mirror gym
    down(beck)
    up(beck)
    down(beck)

    return 0
