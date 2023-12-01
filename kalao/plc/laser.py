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

from time import sleep

from kalao.cacao import aocontrol
from kalao.plc import core
from kalao.timers import database as database_timer
from kalao.utils import database, kalao_time

from opcua import ua

import config


@core.beckhoff_autoconnect
def plc_status(beck=None):
    """
    Query the current status of the laser

    :return: intensity of laser
    """

    device_status_dict = {
        'Status': beck.get_node('ns = 4;s = MAIN.Laser.Status').get_value(),
        'Current': beck.get_node('ns = 4;s = MAIN.Laser.Current').get_value(),
    }

    return device_status_dict


def get_state():
    return plc_status()['Status']


def get_power():
    return plc_status()['Current']


def disable(beck=None):
    """
    Power off laser source

    :return: status of the laser
    """

    return _switch('bDisable', beck=beck)


def enable(beck=None):
    """
    Power on laser source and set to default intensity.
    Disables EM gain on WFS camera.

    :return: status of the laser
    """

    return _switch('bEnable', beck=beck)


def lock(beck=None):
    """
    Lock laser into software only control

    :return: status of the laser lock
    """

    return _switch('bLock', beck=beck)


def unlock(beck=None):
    """
    Lock laser into software only control

    :return: status of the laser lock
    """

    return _switch('bUnlock', beck=beck)


def get_switch_time():
    """
    Looks up the time when the tungsten lamp as last been put into current state (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """

    # Update db to make sure the latest data point is valid
    database_timer.update_monitoring_db()

    data = database.get_time_since_state('monitoring', 'laser_state')

    if data.get('since') is None:
        return data['current']['value'], 0

    return data['current']['value'], (
        kalao_time.now() - data['since']['timestamp']).total_seconds()


@core.beckhoff_autoconnect
def set_intensity(intensity=0.4, beck=None):
    """
    Set light intensity of the laser source

    :param intensity: light intensity to use in ?mW?

    :return: value of the new intensity
    """
    database.store('obs',
                   {'laser_log': f'Setting laser intensity to {intensity}'})

    aocontrol.emgain_off()

    # Limit intensity to protect the WFS
    if intensity > config.Laser.max_intensity:
        intensity = config.Laser.max_intensity
    if not beck.get_node("ns=4;s=MAIN.Laser.bEnable").get_value():
        laser_enable = beck.get_node("ns=4;s=MAIN.Laser.bEnable")
        laser_enable.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                ua.Variant(True,
                           laser_enable.get_data_type_as_variant_type())))

    # Give new intensity value
    laser_setIntensity = beck.get_node("ns=4;s=MAIN.Laser.setIntensity")
    laser_setIntensity.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(float(intensity),
                       laser_setIntensity.get_data_type_as_variant_type())))

    # Apply new intensity value
    laser_bSetIntensity = beck.get_node("ns=4;s=MAIN.Laser.bSetIntensity")
    laser_bSetIntensity.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True,
                       laser_bSetIntensity.get_data_type_as_variant_type())))

    sleep(config.Laser.switch_wait)
    current = beck.get_node("ns=4;s=MAIN.Laser.Current").get_value()

    return current


@core.beckhoff_autoconnect
def _switch(action_name, beck=None):
    """
     Enable or Disable the laser depending on action_name

    :param action_name: bDisable or bEnable
    :return: status of laser
    """

    if action_name == 'bEnable':
        database.store('obs', {'laser_log': 'Enabling laser'})
        aocontrol.emgain_off()
    elif action_name == 'bDisable':
        database.store('obs', {'laser_log': 'Disabling laser'})
        set_intensity(0, beck=beck)
    elif action_name == 'bLock':
        database.store('obs', {'laser_log': 'Locking laser'})
    elif action_name == 'bUnlock':
        database.store('obs', {'laser_log': 'Unlocking laser'})

    laser_switch = beck.get_node("ns = 4; s = MAIN.Laser." + action_name)
    laser_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, laser_switch.get_data_type_as_variant_type())))

    sleep(config.Laser.switch_wait)
    if beck.get_node("ns=4;s=MAIN.Laser.Status").get_value():
        laser_status = 'ON'
    else:
        laser_status = 'OFF'

    return laser_status


def init():
    database.store('obs', {'laser_log': 'Initialising laser'})

    return 0
