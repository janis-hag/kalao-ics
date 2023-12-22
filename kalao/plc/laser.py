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

from kalao.definitions.enums import LaserState

import config


@core.beckhoff_autoconnect
def get_state(beck=None):
    if beck.get_node(f'{config.PLC.Node.LASER}.Status').get_value():
        return LaserState.ON
    else:
        return LaserState.OFF


@core.beckhoff_autoconnect
def get_power(beck=None):
    return beck.get_node(f'{config.PLC.Node.LASER}.Current').get_value()


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

    data = database.get_time_since_state('monitoring', 'laser_state', '==',
                                         get_state().value)

    if data.get('since') is None:
        return data['current']['value'], 0

    return data['current']['value'], (
        kalao_time.now() - data['since']['timestamp']).total_seconds()


@core.beckhoff_autoconnect
def set_power(power, beck=None):
    """
    Set light intensity of the laser source

    :param power: light intensity to use in ?mW?

    :return: value of the new intensity
    """
    database.store('obs', {'laser_log': f'Setting laser intensity to {power}'})

    if power != 0:
        aocontrol.emgain_off()

    # Limit intensity to protect the WFS
    if power > config.Laser.max_power:
        power = config.Laser.max_power

    # Give new intensity value
    laser_setIntensity = beck.get_node(f'{config.PLC.Node.LASER}.setIntensity')
    laser_setIntensity.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(float(power),
                       laser_setIntensity.get_data_type_as_variant_type())))

    # Apply new intensity value
    laser_bSetIntensity = beck.get_node(
        f'{config.PLC.Node.LASER}.bSetIntensity')
    laser_bSetIntensity.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True,
                       laser_bSetIntensity.get_data_type_as_variant_type())))

    sleep(config.Laser.switch_wait)
    current = beck.get_node(f'{config.PLC.Node.LASER}.Current').get_value()

    return current


@core.beckhoff_autoconnect
def _switch(action_name, beck=None):
    """
     Enable or Disable the laser depending on action_name

    :param action_name: bDisable or bEnable
    :return: status of laser
    """

    if action_name == LaserState.ON:
        action_name = 'bEnable'
    elif action_name == LaserState.OFF:
        action_name = 'bDisable'

    if action_name == 'bEnable':
        database.store('obs', {'laser_log': 'Enabling laser'})
        aocontrol.emgain_off()
    elif action_name == 'bDisable':
        database.store('obs', {'laser_log': 'Disabling laser'})
    elif action_name == 'bLock':
        database.store('obs', {'laser_log': 'Locking laser'})
    elif action_name == 'bUnlock':
        database.store('obs', {'laser_log': 'Unlocking laser'})

    laser_switch = beck.get_node(f'{config.PLC.Node.LASER}.{action_name}')
    laser_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, laser_switch.get_data_type_as_variant_type())))

    sleep(config.Laser.switch_wait)

    return get_state(beck=beck)


def init():
    database.store('obs', {'laser_log': 'Initialising laser'})
    database.store('obs', {'laser_log': 'Laser initialised'})

    return 0
