#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : flipmirror
# @Date : 2021-01-02-15-08
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
flipmirror.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import time
from datetime import datetime, timezone

from kalao import database, logger
from kalao.plc import core

from opcua import ua

from kalao.definitions.enums import FlipMirrorPosition, ReturnCode

import config


def down(beck=None):
    """
    Move the flip mirror down

    :return: status of the flipmirror
    """

    return _switch('bDown_Flip', beck=beck)


def up(beck=None):
    """
    Move the flip mirror up

    :return: status of the flipmirror
    """

    return _switch('bUp_Flip', beck=beck)


@core.beckhoff_autoconnect
def _switch(action_name, beck=None):
    """
     Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
    :return: position of flipmirror
    """

    if action_name == FlipMirrorPosition.UP:
        action_name = 'bUp_Flip'
    elif action_name == FlipMirrorPosition.DOWN:
        action_name = 'bDown_Flip'

    if action_name == 'bUp_Flip':
        logger.info('flipmirror', 'Flipping mirror up')
    elif action_name == 'bDown_Flip':
        logger.info('flipmirror', 'Flipping mirror down')

    shutter_switch = beck.get_node(
        f'{config.PLC.Node.FLIP_MIRROR}.{action_name}')
    shutter_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, shutter_switch.get_data_type_as_variant_type())))

    time.sleep(1)

    position = get_position(beck=beck)

    return position


@core.beckhoff_autoconnect
def get_position(beck=None):
    """
    Query the single string status of the shutter.

    :return: single string status of shutter
    """

    # Check error status
    error_code = beck.get_node(
        f'{config.PLC.Node.FLIP_MIRROR}.FlipMirror.stat.nErrorCode').get_value(
        )

    if error_code != 0:
        error_text = beck.get_node(
            f'{config.PLC.Node.FLIP_MIRROR}.FlipMirror.stat.sErrorText'
        ).get_value()

        logger.error('flipmirror', f'{error_text} ({error_code})')

        return FlipMirrorPosition.ERROR

    else:
        if beck.get_node(
                f'{config.PLC.Node.FLIP_MIRROR}.bStatus_Up_Flip').get_value():
            return FlipMirrorPosition.UP
        elif beck.get_node(f'{config.PLC.Node.FLIP_MIRROR}.bStatus_Down_Flip'
                           ).get_value():
            return FlipMirrorPosition.DOWN
        else:
            return FlipMirrorPosition.UNKNOWN


@core.beckhoff_autoconnect
def init(beck=None):
    logger.info('flipmirror', 'Initialising flip mirror')

    # Do the flip mirror gym if needed
    state, switch_time = get_switch_time()
    if switch_time > 86400:
        up(beck=beck)
        down(beck=beck)

    logger.info('flipmirror', 'Flip mirror initialised')

    return ReturnCode.PLC_INIT_SUCCESS


def get_switch_time():
    """
    Looks up the time when the tungsten lamp has last been put into current state (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """

    data = database.get_time_since_state('monitoring', 'flipmirror_position',
                                         '==',
                                         get_position().value)

    if data.get('since') is None:
        return data['current']['value'], 0

    return data['current']['value'], (datetime.now(
        timezone.utc) - data['since']['timestamp']).total_seconds()
