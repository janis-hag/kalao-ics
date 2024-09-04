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

import time
from datetime import datetime, timezone
from enum import StrEnum

from opcua import Client, ua

from kalao.common.enums import ReturnCode, ShutterStatus

from kalao.ics import database, logger
from kalao.ics.hardware import plc

import config


class ShutterCommand(StrEnum):
    OPEN = 'bOpen_Shutter'
    CLOSE = 'bClose_Shutter'


@plc.autoconnect
def get_status(beck: Client = None) -> ShutterStatus:
    """
    Query the single string status of the shutter.

    :return: single string status of shutter
    """

    # Check error status
    error_code = beck.get_node(
        f'{config.PLC.Node.SHUTTER}.Shutter.stat.nErrorCode').get_value()

    if error_code != 0:
        error_text = beck.get_node(
            f'{config.PLC.Node.SHUTTER}.Shutter.stat.sErrorText').get_value()

        logger.error('shutter', f'{error_text} ({error_code})')

        return ShutterStatus.ERROR

    else:
        if beck.get_node(f'{config.PLC.Node.SHUTTER}.bStatus_Closed_Shutter'
                         ).get_value():
            return ShutterStatus.CLOSED
        else:
            return ShutterStatus.OPEN


@plc.autoconnect
def init(beck: Client = None) -> ReturnCode:
    """
    Initialise the shutter.

    :return: status of shutter
    """
    logger.info('shutter', 'Initialising shutter')

    # Do the shutter gym if needed
    state, switch_time = get_switch_time()
    if switch_time > 86400:
        open(beck=beck)
        close(beck=beck)

    logger.info('shutter', 'Shutter initialised')

    return ReturnCode.HW_INIT_SUCCESS


def open(beck: Client = None) -> ShutterStatus:
    """
    Open the shutter.

    :return: status of shutter
    """

    return _switch(ShutterCommand.OPEN, beck=beck)


def close(beck: Client = None) -> ShutterStatus:
    """
    Close the shutter.

    :return: status of shutter
    """

    return _switch(ShutterCommand.CLOSE, beck=beck)


@plc.autoconnect
def _switch(action_name: ShutterCommand | ShutterStatus,
            beck: Client = None) -> ShutterStatus:
    """
     Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
    :return: status of shutter
    """

    if action_name == ShutterStatus.OPEN:
        action_name = ShutterCommand.OPEN
    elif action_name == ShutterStatus.CLOSED:
        action_name = ShutterCommand.CLOSE

    if action_name == ShutterCommand.OPEN:
        logger.info('shutter', 'Opening shutter')
    elif action_name == ShutterCommand.CLOSE:
        logger.info('shutter', 'Closing shutter')

    shutter_switch = beck.get_node(f'{config.PLC.Node.SHUTTER}.{action_name}')
    shutter_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, shutter_switch.get_data_type_as_variant_type())))

    time.sleep(1)

    return get_status(beck=beck)


def get_switch_time() -> tuple[str, float]:
    """
    Looks up the time when the tungsten lamp has last been put into current state (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """

    data = database.get_time_since_state('monitoring', 'shutter_status', '==',
                                         get_status())

    if data.get('since') is None:
        return data['current']['value'], 0

    return data['current']['value'], (datetime.now(
        timezone.utc) - data['since']['timestamp']).total_seconds()
