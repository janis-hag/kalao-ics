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

import os
from configparser import ConfigParser
from pathlib import Path
from time import sleep

from opcua import ua

from kalao.plc import core

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
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
        laser_status = beck.get_node('ns = 4;s = MAIN.Laser.Current').get_value()
    else:
        laser_status = 'OFF'

    if disconnect_on_exit:
        beck.disconnect()

    return laser_status


def disable():
    """
    Power off laser source

    :return: status of the laser
    """

    set_intensity(0)
    laser_status = switch('bDisable')
    return laser_status


def enable():
    """
    Power on laser source

    :return: status of the laser
    """
    laser_status = switch('bEnable')
    return laser_status


def lock():
    """
    Lock laser into software only control

    :return: status of the laser lock
    """
    laser_status = switch('bLock')
    return laser_status


def unlock():
    """
    Lock laser into software only control

    :return: status of the laser lock
    """
    laser_status = switch('bUnlock')
    return laser_status


def set_intensity(intensity=0.04):
    """
    Set light intensity of the laser source

    :param intensity: light intensity to use in ?mW?

    :return: value of the new intensity
    """
    # Connect to OPCUA server
    beck = core.connect()

    # Limit intensity to protect the WFS
    if intensity > MAX_ALLOWED_LASER_INTENSITY:
        intensity = MAX_ALLOWED_LASER_INTENSITY
    if not beck.get_node("ns=4;s=MAIN.Laser.bEnable").get_value():
        laser_enable = beck.get_node("ns=4;s=MAIN.Laser.bEnable")
        laser_enable.set_attribute(
            ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, laser_enable.get_data_type_as_variant_type())))

    # Give new intensity value
    laser_setIntensity = beck.get_node("ns=4;s=MAIN.Laser.setIntensity")
    laser_setIntensity.set_attribute(ua.AttributeIds.Value, ua.DataValue(
        ua.Variant(float(intensity), laser_setIntensity.get_data_type_as_variant_type())))

    # Apply new intensity value
    laser_bSetIntensity = beck.get_node("ns=4;s=MAIN.Laser.bSetIntensity")
    laser_bSetIntensity.set_attribute(
            ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, laser_bSetIntensity.get_data_type_as_variant_type())))

    sleep(LASER_SWITCH_WAIT)
    current = beck.get_node("ns=4;s=MAIN.Laser.Current").get_value()

    beck.disconnect()

    return current


def switch(action_name):
    """
     Enable or Disable the laser depending on action_name

    :param action_name: bDisable or bEnable
    :return: status of laser
    """
    # Connect to OPCUA server
    beck = core.connect()

    laser_switch = beck.get_node("ns = 4; s = MAIN.Laser." + action_name)
    laser_switch.set_attribute(
        ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, laser_switch.get_data_type_as_variant_type())))

    sleep(LASER_SWITCH_WAIT)
    if beck.get_node("ns=4;s=MAIN.Laser.Status").get_value():
        laser_status = 'ON'
    else:
        laser_status = 'OFF'

    beck.disconnect()
    return laser_status


def initialise():
    return 0
