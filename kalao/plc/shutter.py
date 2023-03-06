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

import datetime
import pandas as pd
import numpy as np
from opcua import ua
from time import sleep
from kalao.plc import core
from kalao.utils import database, kalao_time


def status(beck=None):
    """
    Query the status of the shutter

    :return: complete status of shutter
    """

    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    status_dict = core.device_status('Shutter.Shutter', beck=beck)

    if status_dict['sStatus'] == 'STANDING':
        status_dict['sStatus'] = position(beck=beck)

    if disconnect_on_exit:
        beck.disconnect()

    return status_dict


def position(beck=None):
    """
    Query the single string status of the shutter.

    :return: single string status of shutter
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    # Check error status
    error_code = beck.get_node(
            "ns=4; s=MAIN.Shutter.Shutter.stat.nErrorCode").get_value()
    if error_code != 0:
        #someting went wrong
        error_text = beck.get_node(
                "ns=4; s=MAIN.Shutter.Shutter.stat.sErrorText").get_value()
        database.store_obs_log({
                'shutter_log':
                        'ERROR' + str(error_code) + ': ' + str(error_text)
        })

        position_status = error_text

    else:
        if beck.get_node(
                "ns=4; s=MAIN.Shutter.bStatus_Closed_Shutter").get_value():
            bStatus = 'CLOSED'
        else:
            bStatus = 'OPEN'

        position_status = bStatus

    if disconnect_on_exit:
        beck.disconnect()

    return position_status


def initialise(beck=None):
    """
    Initialise the shutter.

    :return: status of shutter
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    init_status = beck.get_node(
            "ns=4; s=MAIN.Shutter.Shutter.stat.nErrorCode").get_value()

    initial_position = position(beck=beck)

    # Do the shutter gym
    if initial_position == 'OPEN':
        shutter_close(beck)
        sleep(3)
        shutter_open(beck)
    elif initial_position == 'CLOSED':
        shutter_open(beck)
        sleep(3)
        shutter_close(beck)

    if disconnect_on_exit:
        beck.disconnect()

    return init_status


def shutter_open(beck=None):
    """
    Open the shutter.

    :return: status of shutter
    """
    log('Opening shutter')
    bStatus = switch('bOpen_Shutter', beck=beck)

    return bStatus


def shutter_close(beck=None):
    """
    Close the shutter.

    :return: status of shutter
    """
    log('Closing shutter')

    bStatus = switch('bClose_Shutter', beck=beck)

    return bStatus


def switch(action_name, beck=None):
    """
     Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
    :return: status of shutter
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    shutter_switch = beck.get_node("ns = 4; s = MAIN.Shutter." + action_name)
    shutter_switch.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            True,
                            shutter_switch.get_data_type_as_variant_type())))

    sleep(1)

    if beck.get_node(
            "ns=4; s=MAIN.Shutter.bStatus_Closed_Shutter").get_value():
        bStatus = 'CLOSED'
    else:
        bStatus = 'OPEN'

    if disconnect_on_exit:
        beck.disconnect()

    return bStatus


def _update_db(beck=None):
    """
    Update the database with the current shutter position

    :param beck: handle to the beckhoff connection if it's already open
    :return:
    """

    database.store_monitoring({'shutter': position(beck=beck)})


def get_switch_time():
    """
    Looks up the time when the tungsten lamp has last been put into current state (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """

    # Update db to make sure the latest data point is valid
    _update_db()
    # Load tungsten log into dataframe
    nb_of_points = 600
    dt = kalao_time.now()

    df = pd.DataFrame(
            database.get_monitoring({'shutter'}, nb_of_points,
                                    dt=dt)['shutter'])
    if len(df) < nb_of_points:
        df = pd.concat([
                df,
                pd.DataFrame(
                        database.get_monitoring({'shutter'}, nb_of_points,
                                                dt=dt -
                                                timedelta(days=1))['shutter'])
        ])

    if len(np.unique(status()['sStatus'])):
        # There is no switch time value
        switch_time = df.iloc[-1]['time_utc']

    else:
        # Search for last occurrence of current status
        switch_time = df.loc[
                df[df['values'] != status()['sStatus']].first_valid_index() -
                1]['time_utc']

    elapsed_time = (kalao_time.now() - switch_time.to_pydatetime().replace(
            tzinfo=datetime.timezone.utc)).total_seconds()

    return elapsed_time


def log(message):
    """
    Log message to shutter_log
    :param message:
    :return:
    """

    database.store_obs_log({'shutter_log': message})

    return 0
