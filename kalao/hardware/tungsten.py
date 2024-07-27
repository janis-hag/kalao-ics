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

from opcua import Client, ua

from kalao import database, logger
from kalao.hardware import plc

from kalao.definitions.enums import IntEnum, ReturnCode, TungstenStatus

import config


class TungstenCommand(IntEnum):
    INIT = 1
    OFF = 2
    ON = 3


def on(beck: Client = None) -> TungstenStatus:
    """
    Turn off tungsten lamp

    :param beck: handle to for the beckhoff connection
    :return: status of the lamp
    """

    return _switch(TungstenCommand.ON, beck=beck)


def off(beck: Client = None) -> TungstenStatus:
    """
    Turn off tungsten lamp

    :param beck: handle to for the beckhoff connection
    :return: status of the lamp
    """

    return _switch(TungstenCommand.OFF, beck=beck)


@plc.autoconnect
def _switch(nCommand_value: TungstenCommand | TungstenStatus,
            beck: Client = None) -> TungstenStatus:
    """
    Send a command to the tungsten lamp

    :param beck: handle to the beckhoff connection
    :param nCommand_value: 1, 2, or 3
    :return:
    """

    if nCommand_value == TungstenStatus.ON:
        nCommand_value = TungstenCommand.ON
    elif nCommand_value == TungstenStatus.OFF:
        nCommand_value = TungstenCommand.OFF

    if nCommand_value == TungstenCommand.ON:
        logger.info('tungsten', 'Turning tungsten lamp on')
    elif nCommand_value == TungstenCommand.OFF:
        logger.info('tungsten', 'Turning tungsten lamp off')

    tungsten_nCommand = beck.get_node(
        f'{config.PLC.Node.TUNGSTEN}.ctrl.nCommand')
    tungsten_bExecute = beck.get_node(
        f'{config.PLC.Node.TUNGSTEN}.ctrl.bExecute')

    previous_status = get_status()

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

    if (nCommand_value == TungstenCommand.ON and previous_status
            != TungstenStatus.ON) or (nCommand_value == TungstenCommand.OFF and
                                      previous_status != TungstenStatus.OFF):
        time.sleep(config.Tungsten.switch_wait)

    return get_status(beck=beck)


@plc.autoconnect
def init(beck: Client = None) -> ReturnCode:
    """
    Initialise the calibration unit.

    :param beck: the handle for the plc connection
    :return: returns 0 on success and error code on failure
    """
    logger.info('tungsten', 'Initialising tungsten lamp')

    # Check if init, if not do init
    if not beck.get_node(
            f'{config.PLC.Node.TUNGSTEN}.stat.bInitialised').get_value():
        _switch(TungstenCommand.INIT, beck=beck)

        time.sleep(config.PLC.init_poll_interval)
        while (beck.get_node(f'{config.PLC.Node.TUNGSTEN}.stat.sStatus').
               get_value() == 'INITIALISING'):
            time.sleep(config.PLC.init_poll_interval)

        if not beck.get_node(
                f'{config.PLC.Node.TUNGSTEN}.stat.bInitialised').get_value():
            logger.error('tungsten', 'Tungsten lamp initialisation failed')
            return ReturnCode.HW_INIT_FAILED

    logger.info('tungsten', 'Tungsten lamp initialised')
    return ReturnCode.HW_INIT_SUCCESS


@plc.autoconnect
def get_status(beck: Client = None) -> TungstenStatus:
    """
    Get the current status of the tungsten lamp.
    """

    # Check error status
    error_code = beck.get_node(
        f'{config.PLC.Node.TUNGSTEN}.stat.nErrorCode').get_value()

    if error_code != 0:
        error_text = beck.get_node(
            f'{config.PLC.Node.TUNGSTEN}.stat.sErrorText').get_value()

        logger.error('tungsten', f'{error_text} ({error_code})')

        return TungstenStatus.ERROR

    else:
        status_plc = beck.get_node(
            f'{config.PLC.Node.TUNGSTEN}.stat.sStatus').get_value()

        if status_plc == 'OFF':
            return TungstenStatus.OFF
        elif status_plc == 'ON':
            return TungstenStatus.ON
        else:
            logger.error('tungsten', f'Unknown status {status_plc}')

            return TungstenStatus.ERROR


def get_switch_time() -> tuple[str, float]:
    """
    Looks up the time when the tungsten lamp as last been put into current status (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """

    data = database.get_time_since_state('monitoring', 'tungsten_status', '==',
                                         get_status())

    if data.get('since') is None:
        return data['current']['value'], 0

    return data['current']['value'], (datetime.now(
        timezone.utc) - data['since']['timestamp']).total_seconds()
