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

from . import core
from opcua import ua
from time import sleep
from configparser       import ConfigParser

# Read config file
parser = ConfigParser()
parser.read('../kalao.config')

MAX_ALLOWED_LASER_INTENSITY = parser.getfloat('PLC','LaserMaxAllowed')


def status(beck=None):
    """
    Query the current intensity of the laser

    :return: intensity of laser
    """
    # Connect to OPCUA server
    if beck is None:
        disconnect_on_exit = True
        beck = core.connect()
    else:
        disconnect_on_exit = False

    laser_status = beck.get_node('ns = 4;s = MAIN.Laser.Current').get_value()

    if disconnect_on_exit:
        beck.disconnect()

    return laser_status


def disable():
    """
    Power off laser source

    :return: status of the laser
    """
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

    sleep(7)
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

    sleep(1)
    if beck.get_node("ns=4;s=MAIN.Laser.bDisable").get_value():
        laser_status = 'OFF'
    else:
        laser_status = 'ON'

    beck.disconnect()
    return laser_status

def initialise():
    return 0
