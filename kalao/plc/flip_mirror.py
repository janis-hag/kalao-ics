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

from kalao.plc import core
from kalao.timers import database as database_timer
from kalao.utils import database, kalao_time

from opcua import ua

from kalao.definitions.enums import FlipMirrorPosition

import config


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

    if action_name == FlipMirrorPosition.UP:
        action_name = 'bUp_Flip'
    elif action_name == FlipMirrorPosition.DOWN:
        action_name = 'bDown_Flip'

    if action_name == 'bUp_Flip':
        database.store('obs', {'flip_mirror_log': 'Flipping mirror up'})
    elif action_name == 'bDown_Flip':
        database.store('obs', {'flip_mirror_log': 'Flipping mirror down'})

    shutter_switch = beck.get_node(
        f'{config.PLC.Node.FLIP_MIRROR}.{action_name}')
    shutter_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, shutter_switch.get_data_type_as_variant_type())))

    sleep(1)

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

        database.store('obs', {
            'flip_mirror_log': f'[ERROR] {error_text} ({error_code})'
        })

        position = FlipMirrorPosition.ERROR

    else:
        if beck.get_node(
                f'{config.PLC.Node.FLIP_MIRROR}.bStatus_Up_Flip').get_value():
            position = FlipMirrorPosition.UP
        elif beck.get_node(f'{config.PLC.Node.FLIP_MIRROR}.bStatus_Down_Flip'
                           ).get_value():
            position = FlipMirrorPosition.DOWN
        else:
            position = FlipMirrorPosition.UNKNOWN

    return position


@core.beckhoff_autoconnect
def init(beck=None):
    database.store('obs', {'flip_mirror_log': 'Initialising flip mirror'})

    # Do the flip mirror gym
    down(beck=beck)
    up(beck=beck)
    down(beck=beck)

    return 0


def get_switch_time():
    """
    Looks up the time when the tungsten lamp has last been put into current state (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """

    # Update db to make sure the latest data point is valid
    database_timer.update_monitoring_db()

    data = database.get_time_since_state('monitoring', 'flip_mirror_position')

    if data.get('since') is None:
        return data['current']['value'], 0

    return data['current']['value'], (
        kalao_time.now() - data['since']['timestamp']).total_seconds()
