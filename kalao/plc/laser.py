#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : laser
# @Date : 2021-01-26-16-48
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
laser.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import datetime
import os
from configparser import ConfigParser
from pathlib import Path
from time import sleep
import pandas as pd
import numpy as np

from opcua import ua

from kalao.plc import core
from kalao.utils import database, kalao_time
from kalao.cacao import aocontrol

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
# Read config file
parser = ConfigParser()
parser.read(config_path)

MAX_ALLOWED_LASER_INTENSITY = parser.getfloat('PLC', 'LaserMaxAllowed')
LASER_SWITCH_WAIT = parser.getfloat('PLC', 'LaserSwitchWait')


def status(beck=None):
    """
    Query the current intensity of the laser

    :return: intensity of laser
    """
    # Connect to OPCUA server
    # if beck is None:
    #     disconnect_on_exit = True
    #     beck = core.connect()
    # else:
    #     disconnect_on_exit = False

    beck, disconnect_on_exit = core.check_beck(beck)

    if beck.get_node('ns = 4;s = MAIN.Laser.Status').get_value():
        laser_status = beck.get_node(
                'ns = 4;s = MAIN.Laser.Current').get_value()
    else:
        laser_status = 'OFF'

    if disconnect_on_exit:
        beck.disconnect()

    return laser_status


def disable(beck=None):
    """
    Power off laser source

    :return: status of the laser
    """

    set_intensity(0, beck=beck)
    laser_status = switch('bDisable', beck=beck)

    return laser_status


def enable(beck=None):
    """
    Power on laser source and set to default intensity.
    Disables EM gain on WFS camera.

    :return: status of the laser
    """

    aocontrol.emgain_off()

    laser_status = switch('bEnable', beck=beck)
    laser_status = set_intensity(beck=beck)

    return laser_status


def lock(beck=None):
    """
    Lock laser into software only control

    :return: status of the laser lock
    """
    laser_status = switch('bLock', beck=beck)
    return laser_status


def unlock(beck=None):
    """
    Lock laser into software only control

    :return: status of the laser lock
    """
    laser_status = switch('bUnlock', beck=beck)
    return laser_status


def get_switch_time():
    """
    Looks up the time when the tungsten lamp as last been put into current state (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """

    # Update db to make sure the latest data point is valid
    _update_db()

    nb_of_points = 600
    dt = kalao_time.now()

    # Load laser log into dataframe
    df = pd.DataFrame(
            database.get_monitoring({'laser'}, nb_of_points, dt=dt)['laser'])

    if len(df) < nb_of_points:
        df = pd.concat([
                df,
                pd.DataFrame(
                        database.get_monitoring({'laser'}, nb_of_points,
                                                dt=dt - datetime.timedelta(
                                                        days=1))['laser'])
        ])

    # Search for last occurence of current status
    if len(np.unique(status())):
        # There is no switch time value
        switch_time = df.iloc[-1]['time_utc']

    else:
        switch_time = df.loc[df[df['values'] != status()].first_valid_index() -
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

    database.store_obs_log({'laser_log': message})

    return 0


def set_intensity(intensity=0.4, beck=None):
    """
    Set light intensity of the laser source

    :param intensity: light intensity to use in ?mW?

    :return: value of the new intensity
    """

    # TODO switch off EMGAIN
    aocontrol.emgain_off()

    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    # Limit intensity to protect the WFS
    if intensity > MAX_ALLOWED_LASER_INTENSITY:
        intensity = MAX_ALLOWED_LASER_INTENSITY
    if not beck.get_node("ns=4;s=MAIN.Laser.bEnable").get_value():
        laser_enable = beck.get_node("ns=4;s=MAIN.Laser.bEnable")
        laser_enable.set_attribute(
                ua.AttributeIds.Value,
                ua.DataValue(
                        ua.Variant(
                                True,
                                laser_enable.get_data_type_as_variant_type())))

    # Give new intensity value
    laser_setIntensity = beck.get_node("ns=4;s=MAIN.Laser.setIntensity")
    laser_setIntensity.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            float(intensity),
                            laser_setIntensity.get_data_type_as_variant_type())
            ))

    # Apply new intensity value
    laser_bSetIntensity = beck.get_node("ns=4;s=MAIN.Laser.bSetIntensity")
    laser_bSetIntensity.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            True,
                            laser_bSetIntensity.get_data_type_as_variant_type(
                            ))))

    sleep(LASER_SWITCH_WAIT)
    current = beck.get_node("ns=4;s=MAIN.Laser.Current").get_value()

    if disconnect_on_exit:
        beck.disconnect()

    return current


def switch(action_name, beck=None):
    """
     Enable or Disable the laser depending on action_name

    :param action_name: bDisable or bEnable
    :return: status of laser
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    laser_switch = beck.get_node("ns = 4; s = MAIN.Laser." + action_name)
    laser_switch.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(True,
                               laser_switch.get_data_type_as_variant_type())))

    sleep(LASER_SWITCH_WAIT)
    if beck.get_node("ns=4;s=MAIN.Laser.Status").get_value():
        laser_status = 'ON'
    else:
        laser_status = 'OFF'

    if disconnect_on_exit:
        beck.disconnect()

    return laser_status


def initialise():
    return 0


def _update_db(beck=None):
    """
    Update the database with the current shutter position

    :param beck: handle to the beckhoff connection if it's already open
    :return:
    """

    database.store_monitoring({'laser': status(beck=beck)})
