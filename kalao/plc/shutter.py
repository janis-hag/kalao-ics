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

from time import sleep

import kalao.plc.core
from kalao.plc import core
from kalao.timers import database as database_timer
from kalao.utils import database, kalao_time

from opcua import ua

from kalao.definitions.enums import ShutterState


@core.beckhoff_autoconnect
def plc_status(beck=None):
    """
    Query the status of the shutter

    :return: complete status of shutter
    """

    status_dict = kalao.plc.core.device_status('Shutter.Shutter', beck=beck)

    if status_dict['sStatus'] == 'STANDING':
        status_dict['sStatus'] = get_state(beck=beck)

    return status_dict


@core.beckhoff_autoconnect
def get_state(beck=None):
    """
    Query the single string status of the shutter.

    :return: single string status of shutter
    """

    # Check error status
    error_code = beck.get_node(
        "ns=4; s=MAIN.Shutter.Shutter.stat.nErrorCode").get_value()

    if error_code != 0:
        error_text = beck.get_node(
            "ns=4; s=MAIN.Shutter.Shutter.stat.sErrorText").get_value()

        database.store('obs',
                       {'shutter_log': f'[ERROR] {error_text} ({error_code})'})

        state = ShutterState.ERROR

    else:
        if beck.get_node(
                "ns=4; s=MAIN.Shutter.bStatus_Closed_Shutter").get_value():
            state = ShutterState.CLOSED
        else:
            state = ShutterState.OPEN

    return state


@core.beckhoff_autoconnect
def init(beck=None):
    """
    Initialise the shutter.

    :return: status of shutter
    """
    database.store('obs', {'shutter_log': 'Initialising shutter'})

    init_status = beck.get_node(
        "ns=4; s=MAIN.Shutter.Shutter.stat.nErrorCode").get_value()

    # Do the shutter gym
    close(beck=beck)
    open(beck=beck)
    close(beck=beck)

    return init_status


def open(beck=None):
    """
    Open the shutter.

    :return: status of shutter
    """

    return _switch('bOpen_Shutter', beck=beck)


def close(beck=None):
    """
    Close the shutter.

    :return: status of shutter
    """

    return _switch('bClose_Shutter', beck=beck)


@core.beckhoff_autoconnect
def _switch(action_name, beck=None):
    """
     Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
    :return: status of shutter
    """

    if action_name == 'bOpen_Shutter':
        database.store('obs', {'shutter_log': 'Opening shutter'})
    elif action_name == 'bClose_Shutter':
        database.store('obs', {'shutter_log': 'Closing shutter'})

    shutter_switch = beck.get_node("ns = 4; s = MAIN.Shutter." + action_name)
    shutter_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, shutter_switch.get_data_type_as_variant_type())))

    sleep(1)

    state = get_state(beck=beck)

    return state


def get_switch_time():
    """
    Looks up the time when the tungsten lamp has last been put into current state (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """

    # Update db to make sure the latest data point is valid
    database_timer.update_monitoring_db()

    data = database.get_time_since_state('monitoring', 'shutter_state')

    if data.get('since') is None:
        return data['current']['value'], 0

    return data['current']['value'], (
        kalao_time.now() - data['since']['timestamp']).total_seconds()
