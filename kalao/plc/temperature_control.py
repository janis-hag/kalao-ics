#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : temperature_control.py
# @Date : 2021-12-07-15-20
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
temperature_control.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import time
from datetime import datetime, timezone

from kalao import database, logger
from kalao.plc import core

from opcua import ua

from kalao.definitions.enums import RelayState

import config


@core.beckhoff_autoconnect
def get_temperatures(beck=None):
    """
    Query all the temperature sensors.

    :param beck: handle of the beckhoff connection
    :return: dictionary of temperatures
    """

    return {
        'temp_bench_air':
            config.PLC.temp_bench_air_offset +
            beck.get_node(config.PLC.Node.TEMP_BENCH_AIR).get_value(),
        'temp_bench_board':
            config.PLC.temp_bench_board_offset +
            beck.get_node(config.PLC.Node.TEMP_BENCH_BOARD).get_value(),
        'temp_water_in':
            config.PLC.temp_water_in_offset +
            beck.get_node(config.PLC.Node.TEMP_WATER_IN).get_value(),
        'temp_water_out':
            config.PLC.temp_water_out_offset +
            beck.get_node(config.PLC.Node.TEMP_WATER_OUT).get_value(),
        'hygro_bench_air':
            beck.get_node(config.PLC.Node.HYGROMETER).get_value(),
    }


@core.beckhoff_autoconnect
def get_cooling_status(beck=None):
    """
    Query status of the cooling system.

    :param beck: handle of the beckhoff connection
    :return:
    """

    cooling_status = {
        'pump_status': pump_status(beck=beck),
        'pump_temp': pump_temperature(beck=beck),
        'heater_status': heater_status(beck=beck),
        'fan_status': fan_status(beck=beck),
        'coolant_flow_rate': get_flow(beck=beck),
    }

    return cooling_status


@core.beckhoff_autoconnect
def get_state(node, beck=None):
    """
    Open or Close the shutter depending on action_name

    :param node: bClose_Shutter or
    :return: position of flipmirror
    """

    if beck.get_node(node).get_value():
        relay_status = RelayState.ON
    else:
        relay_status = RelayState.OFF

    return relay_status


@core.beckhoff_autoconnect
def switch(node, on, beck=None):
    """
     Open or Close the shutter depending on action_name

    :param node: bClose_Shutter or
    :return: position of flipmirror
    """

    if on:
        logger.info('temperature', f'Switching on {node}')
    else:
        logger.info('temperature', f'Switching off {node}')

    relay_switch = beck.get_node(node)
    relay_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(on, relay_switch.get_data_type_as_variant_type())))

    time.sleep(1)

    relay_status = get_state(node, beck=beck)

    return relay_status


def pump_on(beck=None):
    """
    Convenience function to turn on the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """

    return switch(config.PLC.Node.PUMP, True, beck=beck)


def pump_off(beck=None):
    """
    Convenience function to turn off the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """

    return switch(config.PLC.Node.PUMP, False, beck=beck)


def pump_status(beck=None):
    """
    Convenience function to query the status of the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """

    return get_state(config.PLC.Node.PUMP, beck=beck)


@core.beckhoff_autoconnect
def pump_temperature(beck=None):
    """
    Convenience function to query the temperature of the pump

    :param beck: beck: handle to the beckhoff connection
    :return: temperature of the pump in degrees
    """

    pump_temp = beck.get_node(config.PLC.Node.TEMP_PUMP).get_value()

    return pump_temp


def heater_on(beck=None):
    """
    Convenience function to turn on the water heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """

    return switch(config.PLC.Node.HEATER, True, beck=beck)


def heater_off(beck=None):
    """
    Convenience function to turn off the water heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """

    return switch(config.PLC.Node.HEATER, False, beck=beck)


def heater_status(beck=None):
    """
    Convenience function to query the status of the water heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """

    return get_state(config.PLC.Node.HEATER, beck=beck)


def fan_on(beck=None):
    """
    Convenience function to turn on the water fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return switch(config.PLC.Node.FAN, True, beck=beck)


def fan_off(beck=None):
    """
    Convenience function to turn off the water fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return switch(config.PLC.Node.FAN, False, beck=beck)


def fan_status(beck=None):
    """
    Convenience function to query the status of the water fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return get_state(config.PLC.Node.FAN, beck=beck)


def get_flow_threshold_time(flow_threshold, beck=None):
    """
    Looks up the time when the flow was under a given threshold

    :return:  switch_time a datetime object
    """

    data = database.get_time_since_state('monitoring', 'coolant_flow_rate',
                                         '>=', flow_threshold)

    if data.get('since') is None:
        return 0

    return (datetime.now(timezone.utc) -
            data['since']['timestamp']).total_seconds()


@core.beckhoff_autoconnect
def get_flow(beck=None):
    """
    Convenience function to query the value of the water flow from the flowmeter

    TODO: add rounding of returned value

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return beck.get_node(config.PLC.Node.FLOWMETER).get_value()
