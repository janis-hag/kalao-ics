#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : cooling.py
# @Date : 2021-12-07-15-20
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
cooling.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import time
from typing import Any

from kalao import logger
from kalao.hardware import plc

from opcua import Client, ua

from kalao.definitions.enums import RelayState, ReturnCode

import config


class RelayCommand:
    OFF = False
    ON = True


@plc.autoconnect
def get_all_status(beck: Client = None) -> dict[str, Any]:
    """
    Query status of the cooling system.

    :param beck: handle of the beckhoff connection
    :return:
    """

    cooling_status = {
        'pump_status':
            pump_status(beck=beck),
        'pump_temp':
            pump_temperature(beck=beck),
        'heater_status':
            heater_status(beck=beck),
        'heatexchanger_fan_status':
            heatexchanger_fan_status(beck=beck),
        'coolant_flowrate':
            get_flowrate(beck=beck),
        'coolant_temp_in':
            config.PLC.coolant_temp_in_offset +
            beck.get_node(config.PLC.Node.COOLANT_TEMP_IN).get_value(),
        'coolant_temp_out':
            config.PLC.coolant_temp_out_offset +
            beck.get_node(config.PLC.Node.COOLANT_TEMP_OUT).get_value(),
    }

    return cooling_status


@plc.autoconnect
def get_state(node: str, beck: Client = None) -> RelayState:
    if beck.get_node(node).get_value():
        return RelayState.ON
    else:
        return RelayState.OFF


@plc.autoconnect
def switch(node: str, action_name: RelayCommand | RelayState,
           beck: Client = None) -> RelayState:

    if action_name == RelayState.ON:
        action_name = RelayCommand.ON
    elif action_name == RelayState.OFF:
        action_name = RelayCommand.OFF

    if action_name == RelayCommand.ON:
        logger.info('cooling', f'Switching on {node}')
    elif action_name == RelayCommand.OFF:
        logger.info('cooling', f'Switching off {node}')

    relay_switch = beck.get_node(node)
    relay_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(action_name,
                       relay_switch.get_data_type_as_variant_type())))

    time.sleep(1)

    return get_state(node, beck=beck)


def pump_on(beck: Client = None) -> RelayState:
    """
    Convenience function to turn on the coolant pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """

    return switch(config.PLC.Node.PUMP, RelayState.ON, beck=beck)


def pump_off(beck: Client = None) -> RelayState:
    """
    Convenience function to turn off the coolant pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """

    return switch(config.PLC.Node.PUMP, RelayState.OFF, beck=beck)


def pump_status(beck: Client = None) -> RelayState:
    """
    Convenience function to query the status of the coolant pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """

    return get_state(config.PLC.Node.PUMP, beck=beck)


@plc.autoconnect
def pump_temperature(beck: Client = None) -> float:
    """
    Convenience function to query the temperature of the pump

    :param beck: beck: handle to the beckhoff connection
    :return: temperature of the pump in degrees
    """

    pump_temp = beck.get_node(config.PLC.Node.PUMP_TEMP).get_value()

    return pump_temp


def heater_on(beck: Client = None) -> RelayState:
    """
    Convenience function to turn on the coolant heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """

    return switch(config.PLC.Node.HEATER, RelayState.ON, beck=beck)


def heater_off(beck: Client = None) -> RelayState:
    """
    Convenience function to turn off the coolant heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """

    return switch(config.PLC.Node.HEATER, RelayState.OFF, beck=beck)


def heater_status(beck: Client = None) -> RelayState:
    """
    Convenience function to query the status of the coolant heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """

    return get_state(config.PLC.Node.HEATER, beck=beck)


def heatexchanger_fan_on(beck: Client = None) -> RelayState:
    """
    Convenience function to turn on the coolant fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return switch(config.PLC.Node.HEAT_EXCHANGER_FAN, RelayState.ON, beck=beck)


def heatexchanger_fan_off(beck: Client = None) -> RelayState:
    """
    Convenience function to turn off the coolant fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return switch(config.PLC.Node.HEAT_EXCHANGER_FAN, RelayState.OFF,
                  beck=beck)


def heatexchanger_fan_status(beck: Client = None) -> RelayState:
    """
    Convenience function to query the status of the coolant fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return get_state(config.PLC.Node.HEAT_EXCHANGER_FAN, beck=beck)


@plc.autoconnect
def get_flowrate(beck: Client = None) -> float:
    """
    Convenience function to query the value of the coolant flow from the flowmeter

    TODO: add rounding of returned value

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return beck.get_node(config.PLC.Node.FLOWMETER).get_value()


@plc.autoconnect
def init(beck: Client = None) -> ReturnCode:
    logger.info('cooling', 'Initialising cooling system')

    error = False

    for node in [
            config.PLC.Node.HEAT_EXCHANGER_FAN, config.PLC.Node.PUMP,
            config.PLC.Node.HEATER
    ]:
        if node in config.PLC.initial_state:
            state = config.PLC.initial_state[node]
            if switch(node, state, beck=beck) != state:
                error = True

    if error:
        logger.info('cooling', 'Cooling system initialisation failed')
        return ReturnCode.HW_INIT_FAILED
    else:
        logger.info('cooling', 'Cooling system initialised')
        return ReturnCode.HW_INIT_SUCCESS
