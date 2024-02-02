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

import time
from datetime import datetime, timezone

from kalao import database, logger
from kalao.plc import core

from opcua import ua

from kalao.definitions.enums import IntEnum, ReturnCode, TungstenState

import config


class TungstenCommand(IntEnum):
    INIT = 1
    OFF = 2
    ON = 3


def on(beck=None):
    """
    Turn off tungsten lamp

    :param beck: handle to for the beckhoff connection
    :return: status of the lamp
    """

    return send_command(TungstenCommand.ON, beck=beck)


def off(beck=None):
    """
    Turn off tungsten lamp

    :param beck: handle to for the beckhoff connection
    :return: status of the lamp
    """

    return send_command(TungstenCommand.OFF, beck=beck)


@core.beckhoff_autoconnect
def send_command(nCommand_value, beck=None):
    """
    Send a command to the tungsten lamp

    :param beck: handle to the beckhoff connection
    :param nCommand_value: 1, 2, or 3
    :return:
    """

    if nCommand_value == TungstenState.ON:
        nCommand_value = TungstenCommand.ON
    elif nCommand_value == TungstenState.OFF:
        nCommand_value = TungstenCommand.OFF

    if nCommand_value == TungstenCommand.ON:
        logger.info('tungsten', 'Turning tungsten lamp on')
    elif nCommand_value == TungstenCommand.OFF:
        logger.info('tungsten', 'Turning tungsten lamp off')

    tungsten_nCommand = beck.get_node(
        f'{config.PLC.Node.TUNGSTEN}.ctrl.nCommand')
    tungsten_bExecute = beck.get_node(
        f'{config.PLC.Node.TUNGSTEN}.ctrl.bExecute')

    previous_state = get_state()

    tungsten_nCommand.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(int(nCommand_value),
                       tungsten_nCommand.get_data_type_as_variant_type())))

    # Execute
    tungsten_bExecute.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True,
                       tungsten_bExecute.get_data_type_as_variant_type())))

    if nCommand_value == TungstenCommand.ON and previous_state != nCommand_value:
        time.sleep(config.Tungsten.switch_wait)

    return get_state(beck=beck)


@core.beckhoff_autoconnect
def init(beck=None):
    """
    Initialise the calibration unit.

    :param beck: the handle for the plc connection
    :return: returns 0 on success and error code on failure
    """
    logger.info('tungsten', 'Initialising tungsten lamp')

    # Check if init, if not do init
    if not beck.get_node(
            f'{config.PLC.Node.TUNGSTEN}.stat.bInitialised').get_value():
        send_command(TungstenCommand.INIT, beck=beck)

        time.sleep(config.PLC.init_poll_interval)
        while (beck.get_node(f'{config.PLC.Node.TUNGSTEN}.stat.sStatus').
               get_value() == 'INITIALISING'):
            time.sleep(config.PLC.init_poll_interval)

        if not beck.get_node(
                f'{config.PLC.Node.TUNGSTEN}.stat.bInitialised').get_value():
            logger.error('tungsten', 'Tungsten lamp initialisation failed')
            return ReturnCode.PLC_INIT_FAILED

    logger.info('tungsten', 'Tungsten lamp initialised')
    return ReturnCode.PLC_INIT_SUCCESS


@core.beckhoff_autoconnect
def get_state(beck=None):
    """
    Get the current state of the tungsten lamp.
    """

    # Check error status
    error_code = beck.get_node(
        f'{config.PLC.Node.TUNGSTEN}.stat.nErrorCode').get_value()

    if error_code != 0:
        error_text = beck.get_node(
            f'{config.PLC.Node.TUNGSTEN}.stat.sErrorText').get_value()

        logger.error('tungsten', f'{error_text} ({error_code})')

        return TungstenState.ERROR

    else:
        state_plc = beck.get_node(
            f'{config.PLC.Node.TUNGSTEN}.stat.sStatus').get_value()

        if state_plc == 'OFF':
            return TungstenState.OFF
        elif state_plc == 'ON':
            return TungstenState.ON
        else:
            logger.error('tungsten', f'Unknown state {state_plc}')

            return TungstenState.ERROR


def get_switch_time():
    """
    Looks up the time when the tungsten lamp as last been put into current state (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """

    data = database.get_time_since_state('monitoring', 'tungsten_state', '==',
                                         get_state().value)

    if data.get('since') is None:
        return data['current']['value'], 0

    return data['current']['value'], (datetime.now(
        timezone.utc) - data['since']['timestamp']).total_seconds()
