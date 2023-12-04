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

from opcua import ua

from kalao.definitions.enums import IntEnum, TungstenState

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

    if nCommand_value == TungstenCommand.ON:
        database.store('obs', {'tungsten_log': f'Turning tungsten lamp on'})
    elif nCommand_value == TungstenCommand.OFF:
        database.store('obs', {'tungsten_log': f'Turning tungsten lamp off'})

    tungsten_nCommand = beck.get_node("ns=4; s=MAIN.Tungsten.ctrl.nCommand")
    tungsten_bExecute = beck.get_node("ns=4; s=MAIN.Tungsten.ctrl.bExecute")

    tungsten_nCommand.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(int(nCommand_value),
                       tungsten_nCommand.get_data_type_as_variant_type())))

    # Execute
    core.motor_send_execute(tungsten_bExecute)

    sleep(config.Tungsten.switch_wait)

    return get_state(beck=beck)


@core.beckhoff_autoconnect
def init(beck=None):
    """
    Initialise the calibration unit.

    :param beck: the handle for the plc connection
    :return: returns 0 on success and error code on failure
    """
    database.store('obs', {'tungsten_log': f'Initialising tungsten lamp'})

    tungsten_status = 'ERROR'

    # Check if init, if not do init
    if not beck.get_node(
            "ns=4; s=MAIN.Tungsten.stat.bInitialised").get_value():
        # init
        send_command(TungstenCommand.INIT, beck=beck)

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
            tungsten_status = 0
    else:
        tungsten_status = 0

    return tungsten_status


@core.beckhoff_autoconnect
def get_state(beck=None):
    """
    Query the single string status of the shutter.

    :return: single string status of shutter
    """

    # Check error status
    error_code = beck.get_node(
        "ns=4; s=MAIN.Shutter.Tungsten.stat.nErrorCode").get_value()

    if error_code != 0:
        error_text = beck.get_node(
            "ns=4; s=MAIN.Shutter.Tungsten.stat.sErrorText").get_value()

        database.store('obs', {
            'tungsten_log': f'[ERROR] {error_text} ({error_code})'
        })

        state = TungstenState.ERROR

    else:
        state_plc = beck.get_node(
            "ns=4; s=MAIN.Tungsten.stat.sStatus").get_value()

        if state_plc == 'OFF':
            state = TungstenState.OFF
        elif state_plc == 'ON':
            state = TungstenState.ON
        else:
            database.store('obs', {
                'tungsten_log': f'[ERROR] Unknown state {state_plc}'
            })

            state = TungstenState.ERROR

    return state


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
