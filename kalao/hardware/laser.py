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
import math
import time
from datetime import datetime, timezone
from enum import StrEnum

from kalao import database, logger
from kalao.cacao import aocontrol
from kalao.hardware import plc

from opcua import Client, ua

from kalao.definitions.enums import LaserState, ReturnCode

import config


class LaserCommand(StrEnum):
    DISABLE = 'bDisable'
    ENABLE = 'bEnable'
    LOCK = 'bLock'
    UNLOCK = 'bUnlock'


@plc.autoconnect
def get_state(beck: Client = None) -> LaserState:
    if beck.get_node(f'{config.PLC.Node.LASER}.Status').get_value():
        return LaserState.ON
    else:
        return LaserState.OFF


@plc.autoconnect
def get_power(beck: Client = None) -> float:
    return beck.get_node(f'{config.PLC.Node.LASER}.Current').get_value()


def disable(beck: Client = None) -> LaserState:
    """
    Power off laser source

    :return: status of the laser
    """

    return _switch(LaserCommand.DISABLE, beck=beck)


def enable(beck: Client = None) -> LaserState:
    """
    Power on laser source and set to default intensity.
    Disables EM gain on WFS camera.

    :return: status of the laser
    """

    return _switch(LaserCommand.ENABLE, beck=beck)


def lock(beck: Client = None) -> LaserState:
    """
    Lock laser into software only control

    :return: status of the laser lock
    """

    return _switch(LaserCommand.LOCK, beck=beck)


def unlock(beck: Client = None) -> LaserState:
    """
    Lock laser into software only control

    :return: status of the laser lock
    """

    return _switch(LaserCommand.UNLOCK, beck=beck)


def get_switch_time() -> tuple[str, float]:
    """
    Looks up the time when the tungsten lamp as last been put into current state (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """

    data = database.get_time_since_state('monitoring', 'laser_state', '==',
                                         get_state())

    if data.get('since') is None:
        return data['current']['value'], 0

    return data['current']['value'], (datetime.now(
        timezone.utc) - data['since']['timestamp']).total_seconds()


@plc.autoconnect
def set_power(power: float, enable: bool = False,
              beck: Client = None) -> float:
    """
    Set light intensity of the laser source

    :param power: light intensity to use in ?mW?

    :return: value of the new intensity
    """
    logger.info('laser', f'Setting laser power to {power}')

    if power != 0:
        aocontrol.emgain_off()

    # Limit intensity to protect the WFS
    if power > config.Laser.max_power:
        power = config.Laser.max_power

    previous_power = get_power(beck=beck)
    previous_state = get_state(beck=beck)

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

    if enable and previous_state != LaserState.ON:
        _switch(LaserCommand.ENABLE, beck=beck)

    if power != 0 and not math.isclose(
            previous_power, power) and previous_state == LaserState.ON:
        time.sleep(config.Laser.switch_wait)

    return get_power(beck=beck)


@plc.autoconnect
def _switch(action_name: LaserCommand | LaserState,
            beck: Client = None) -> LaserState:
    """
     Enable or Disable the laser depending on action_name

    :param action_name: bDisable or bEnable
    :return: status of laser
    """

    if action_name == LaserState.ON:
        action_name = LaserCommand.ENABLE
    elif action_name == LaserState.OFF:
        action_name = LaserCommand.DISABLE

    if action_name == LaserCommand.ENABLE:
        logger.info('laser', 'Enabling laser')
        aocontrol.emgain_off()
    elif action_name == LaserCommand.DISABLE:
        logger.info('laser', 'Disabling laser')
    elif action_name == LaserCommand.LOCK:
        logger.info('laser', 'Locking laser')
    elif action_name == LaserCommand.UNLOCK:
        logger.info('laser', 'Unlocking laser')

    previous_state = get_state()

    laser_switch = beck.get_node(f'{config.PLC.Node.LASER}.{action_name}')
    laser_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, laser_switch.get_data_type_as_variant_type())))

    if (action_name == LaserCommand.ENABLE and previous_state
            != LaserState.ON) or (action_name == LaserCommand.DISABLE and
                                  previous_state != LaserState.OFF):
        time.sleep(config.Laser.switch_wait)

    return get_state(beck=beck)


def init() -> ReturnCode:
    logger.info('laser', 'Initialising laser')
    logger.info('laser', 'Laser initialised')

    return ReturnCode.HW_INIT_SUCCESS
