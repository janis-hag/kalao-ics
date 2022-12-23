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

import datetime
from opcua import ua
from time import sleep
import pandas as pd
from configparser import ConfigParser
from pathlib import Path
import os

from kalao.plc import core, filterwheel
from kalao.utils import database, kalao_time

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
# Read config file
parser = ConfigParser()
parser.read(config_path)

TungstenSwitchWait = parser.getfloat('PLC', 'TungstenSwitchWait')

node_path = 'Tungsten'


def get_flat_dits():
    Id_filter_dict = filterwheel.create_filter_id()
    Flat_dit_dict = {}
    for key, val in parser.items('LampFlat'):
        # Create dit dictionary based on named filters
        Flat_dit_dict[key] = float(val)
        # Create dit dictionary based on numbered filters
        Flat_dit_dict[Id_filter_dict[key]] = float(val)
    return Flat_dit_dict


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

    state = send_command(beck, 3)

    return state


def off(beck=None):
    """
    Turn off tungsten lamp

    :param beck: handle to for the beckhoff connection
    :return: status of the lamp
    """

    state = send_command(beck, 2)

    return state


def send_command(beck, nCommand_value):
    """
    Send a command to the tungsten lamp

    tungsten number commands are
    1 = init
    2 = OFF
    3 = ON

    :param beck: handle to the beckhoff connection
    :param nCommand_value: 1, 2, or 3
    :return:
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    tungsten_nCommand = beck.get_node("ns=4; s=MAIN.Tungsten.ctrl.nCommand")

    tungsten_nCommand.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            int(nCommand_value),
                            tungsten_nCommand.get_data_type_as_variant_type()))
    )
    # Execute
    send_execute(beck)

    sleep(TungstenSwitchWait)
    state = beck.get_node("ns=4; s=MAIN.Tungsten.stat.sStatus").get_value()

    # Store new status in database
    update_db(beck=beck)

    if disconnect_on_exit:
        beck.disconnect()

    return state


def initialise(beck=None, tungsten_nCommand=None):
    """
    Initialise the calibration unit.

    :param beck: the handle for the plc connection
    :param tungsten_nCommand: handle to send commands to the motor
    :return: returns 0 on success and error code on failure
    """
    if beck is None:
        # Connect to OPCUA server
        disconnect_on_exit = True
        beck = core.connect()
    else:
        disconnect_on_exit = False
    # if tungsten_nCommand is None:
    #     # define commands
    tungsten_status = 'ERROR'

    # Check if init, if not do init
    if not beck.get_node(
            "ns=4; s=MAIN.Tungsten.stat.bInitialised").get_value():
        # init
        send_command(beck, 1)
        sleep(15)
        while (beck.get_node("ns=4; s=MAIN.Tungsten.stat.sStatus").get_value()
               == 'INITIALISING'):
            sleep(15)
        if not beck.get_node(
                "ns=4; s=MAIN.Tungsten.stat.bInitialised").get_value():
            tungsten_status = 'ERROR: ' + str(
                    beck.get_node("ns=4; s=MAIN.Tungsten.stat.nErrorCode").
                    get_value())
        else:
            tungsten_status = beck.get_node(
                    "ns=4; s=MAIN.Tungsten.stat.sStatus").get_value()
    else:
        tungsten_status = 0

    update_db(beck=beck)

    if disconnect_on_exit:
        beck.disconnect()

    return tungsten_status


def send_execute(beck):
    tungsten_bExecute = beck.get_node("ns=4; s=MAIN.Tungsten.ctrl.bExecute")

    tungsten_bExecute.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            True,
                            tungsten_bExecute.get_data_type_as_variant_type()))
    )


def status(beck=None):
    """
    Query the status of the tungsten lamp.

    :return: complete status of tungsten lamp
    """

    node_path = 'Tungsten'

    # Connect to OPCUA server
    if beck is None:
        disconnect_on_exit = True
        beck = core.connect()
    else:
        disconnect_on_exit = False

    device_status_dict = {
            'sStatus':
                    beck.get_node("ns=4; s=MAIN." + node_path +
                                  ".stat.sStatus").get_value(),
            'sErrorText':
                    beck.get_node("ns=4; s=MAIN." + node_path +
                                  ".stat.sErrorText").get_value(),
            'nErrorCode':
                    beck.get_node("ns=4; s=MAIN." + node_path +
                                  ".stat.nErrorCode").get_value(),
            'nStatus':
                    beck.get_node("ns=4; s=MAIN." + node_path +
                                  ".stat.nStatus").get_value()
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
    update_db()
    # Load tungsten log into dataframe
    df = pd.DataFrame(database.get_monitoring({'tungsten'}, 1500)['tungsten'])

    # Search for last occurence of current status
    switch_time = df.loc[
            df[df['values'] != status()['sStatus']].first_valid_index() -
            1]['time_utc']

    elapsed_time = (
            kalao_time.now() -
            switch_time.replace(tzinfo=datetime.timezone.utc)).total_seconds()

    return elapsed_time


def update_db(beck=None):

    database.store_monitoring({'tungsten': status(beck=beck)['sStatus']})


# def switch(action_name):
#     """
#      Open or Close the shutter depending on action_name
#
#     :param action_name: bClose_Shutter or
#     :return: position of flipmirror
#     """
#     # Connect to OPCUA server
#     beck = core.connect()
#
#     tungsten_switch = beck.get_node("ns = 4; s = MAIN.Tungsten." + action_name)
#     tungsten_switch.set_attribute(
#         ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, tungsten_switch.get_data_type_as_variant_type())))
#
#     sleep(1)
#     tungsten_status = beck.get_node("ns=4; s=MAIN." + node_path + ".stat.sStatus").get_value()
#
#     # Store new status in database
#     update_db(beck=beck)
#
#     beck.disconnect()
#
#
#     return tungsten_status

# def send_init(beck, tungsten_nCommand):
#     tungsten_nCommand.set_attribute(ua.AttributeIds.Value,
#                                  ua.DataValue(ua.Variant(int(1), tungsten_nCommand.get_data_type_as_variant_type())))
#     # Execute
#     send_execute(beck)
