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

from time import sleep

from kalao.plc import core
from kalao.timers import database as database_timer
from kalao.utils import database, kalao_time

from kalao.definitions.enums import IntEnum
from opcua import ua

import config


class TungstenCommand(IntEnum):
    INIT = 1
    OFF = 2
    ON = 3


def check_error(beck):
    if beck.get_node("ns=4; s=MAIN.Tungsten.stat.sErrorText").get_value() == 0:
        return 0
    else:
        error_status = 'ERROR'
        return error_status


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


def send_command(nCommand_value, beck=None):
    """
    Send a command to the tungsten lamp

    :param beck: handle to the beckhoff connection
    :param nCommand_value: 1, 2, or 3
    :return:
    """

    if nCommand_value == TungstenCommand.ON:
        database.store('obs', {'tungsten_log': f'Turning tungsten lamp on'})
    elif nCommand_value == TungstenCommand.OFF:
        database.store('obs', {'tungsten_log': f'Turning tungsten lamp off'})

    beck, disconnect_on_exit = core.check_beck(beck)

    tungsten_nCommand = beck.get_node("ns=4; s=MAIN.Tungsten.ctrl.nCommand")

    tungsten_nCommand.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(int(nCommand_value),
                       tungsten_nCommand.get_data_type_as_variant_type())))
    # Execute
    send_execute(beck)

    sleep(config.Tungsten.switch_wait)
    state = beck.get_node("ns=4; s=MAIN.Tungsten.stat.sStatus").get_value()

    if disconnect_on_exit:
        beck.disconnect()

    return state


def init(beck=None):
    """
    Initialise the calibration unit.

    :param beck: the handle for the plc connection
    :return: returns 0 on success and error code on failure
    """
    database.store('obs', {'tungsten_log': f'Initialising tungsten lamp'})

    beck, disconnect_on_exit = core.check_beck(beck)

    tungsten_status = 'ERROR'

    # Check if init, if not do init
    if not beck.get_node(
            "ns=4; s=MAIN.Tungsten.stat.bInitialised").get_value():
        # init
        send_command(TungstenCommand.INIT, beck)
        sleep(15)
        while (beck.get_node("ns=4; s=MAIN.Tungsten.stat.sStatus").get_value()
               == 'INITIALISING'):
            sleep(15)
        if not beck.get_node(
                "ns=4; s=MAIN.Tungsten.stat.bInitialised").get_value():
            tungsten_status = '[ERROR] ' + str(
                beck.get_node(
                    "ns=4; s=MAIN.Tungsten.stat.nErrorCode").get_value())
        else:
            tungsten_status = beck.get_node(
                "ns=4; s=MAIN.Tungsten.stat.sStatus").get_value()
    else:
        tungsten_status = 0

    if disconnect_on_exit:
        beck.disconnect()

    return tungsten_status


def send_execute(beck):
    tungsten_bExecute = beck.get_node("ns=4; s=MAIN.Tungsten.ctrl.bExecute")

    tungsten_bExecute.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True,
                       tungsten_bExecute.get_data_type_as_variant_type())))


def plc_status(beck=None):
    """
    Query the status of the tungsten lamp.

    :return: complete status of tungsten lamp
    """

    beck, disconnect_on_exit = core.check_beck(beck)

    device_status_dict = {
        'sStatus':
            beck.get_node("ns=4; s=MAIN.Tungsten.stat.sStatus").get_value(),
        'sErrorText':
            beck.get_node("ns=4; s=MAIN.Tungsten.stat.sErrorText").get_value(),
        'nErrorCode':
            beck.get_node("ns=4; s=MAIN.Tungsten.stat.nErrorCode").get_value(),
        'nStatus':
            beck.get_node("ns=4; s=MAIN.Tungsten.stat.nStatus").get_value()
    }

    if disconnect_on_exit:
        beck.disconnect()

    return device_status_dict


def get_switch_time():
    """
    Looks up the time when the tungsten lamp as last been put into current state (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """

    # Update db to make sure the latest data point is valid
    database_timer.update_monitoring_db()

    data = database.get_time_since_state('monitoring', 'tungsten_state')

    if data.get('since') is None:
        return data['current']['value'], 0

    return data['current']['value'], (
        kalao_time.now() - data['since']['timestamp']).total_seconds()
