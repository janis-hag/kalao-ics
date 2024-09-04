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

import numpy as np

from opcua import Client, ua

from kalao.common.enums import LaserStatus, ReturnCode

from kalao.ics import database, logger
from kalao.ics.hardware import plc, wfs

import config


class LaserCommand(StrEnum):
    DISABLE = 'bDisable'
    ENABLE = 'bEnable'
    LOCK = 'bLock'
    UNLOCK = 'bUnlock'


@plc.autoconnect
def get_status(beck: Client = None) -> LaserStatus:
    for retry in range(config.Laser.retries):
        status = beck.get_node(f'{config.PLC.Node.LASER}.Status').get_value()

        if status == 1:
            return LaserStatus.ON
        elif status == 0:
            return LaserStatus.OFF
        else:
            time.sleep(config.Laser.retry_wait)
            continue

    return LaserStatus.ERROR


@plc.autoconnect
def get_power(beck: Client = None) -> float:
    for retry in range(config.Laser.retries):
        power = beck.get_node(f'{config.PLC.Node.LASER}.Current').get_value()

        if power < 0:
            time.sleep(config.Laser.retry_wait)
            continue

        return power

    return np.nan


def disable(beck: Client = None) -> LaserStatus:
    """
    Power off laser source

    :return: status of the laser
    """

    return _switch(LaserCommand.DISABLE, beck=beck)


def enable(beck: Client = None) -> LaserStatus:
    """
    Power on laser source and set to default intensity.
    Disables EM gain on WFS camera.

    :return: status of the laser
    """

    return _switch(LaserCommand.ENABLE, beck=beck)


def lock(beck: Client = None) -> LaserStatus:
    """
    Lock laser into software only control

    :return: status of the laser lock
    """

    return _switch(LaserCommand.LOCK, beck=beck)


def unlock(beck: Client = None) -> LaserStatus:
    """
    Lock laser into software only control

    :return: status of the laser lock
    """

    return _switch(LaserCommand.UNLOCK, beck=beck)


def get_switch_time() -> tuple[str, float]:
    data = database.get_time_since_state('monitoring', 'laser_status', '==',
                                         get_status())

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
        wfs.emgain_off()

    # Limit intensity to protect the WFS
    if power > config.Laser.max_power:
        power = config.Laser.max_power

    previous_power = get_power(beck=beck)
    previous_status = get_status(beck=beck)

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

    if enable and previous_status != LaserStatus.ON:
        _switch(LaserCommand.ENABLE, beck=beck)

    if power != 0 and not math.isclose(
            previous_power, power) and previous_status == LaserStatus.ON:
        time.sleep(config.Laser.switch_wait)

    return get_power(beck=beck)


@plc.autoconnect
def _switch(action_name: LaserCommand | LaserStatus,
            beck: Client = None) -> LaserStatus:
    """
     Enable or Disable the laser depending on action_name

    :param action_name: bDisable or bEnable
    :return: status of laser
    """

    if action_name == LaserStatus.ON:
        action_name = LaserCommand.ENABLE
    elif action_name == LaserStatus.OFF:
        action_name = LaserCommand.DISABLE

    if action_name == LaserCommand.ENABLE:
        logger.info('laser', 'Enabling laser')
        wfs.emgain_off()
    elif action_name == LaserCommand.DISABLE:
        logger.info('laser', 'Disabling laser')
    elif action_name == LaserCommand.LOCK:
        logger.info('laser', 'Locking laser')
    elif action_name == LaserCommand.UNLOCK:
        logger.info('laser', 'Unlocking laser')

    previous_status = get_status()

    laser_switch = beck.get_node(f'{config.PLC.Node.LASER}.{action_name}')
    laser_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, laser_switch.get_data_type_as_variant_type())))

    if (action_name == LaserCommand.ENABLE and previous_status
            != LaserStatus.ON) or (action_name == LaserCommand.DISABLE and
                                   previous_status != LaserStatus.OFF):
        time.sleep(config.Laser.switch_wait)

    return get_status(beck=beck)


def init() -> ReturnCode:
    logger.info('laser', 'Initialising laser')
    logger.info('laser', 'Laser initialised')

    return ReturnCode.HW_INIT_SUCCESS
