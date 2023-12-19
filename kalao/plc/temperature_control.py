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

from time import sleep

from kalao.fli import camera
from kalao.plc import core
from kalao.utils import database, kalao_time

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

    temp_values = {
        'temp_bench_air':
            config.PLC.temp_bench_air_offset +
            beck.get_node(config.PLC.Node.TEMP_BENCH_AIR).get_value() / 10,
        'temp_bench_board':
            config.PLC.temp_bench_board_offset +
            beck.get_node(config.PLC.Node.TEMP_BENCH_BOARD).get_value() / 10,
        'temp_water_in':
            config.PLC.temp_water_in_offset +
            beck.get_node(config.PLC.Node.TEMP_WATER_IN).get_value() / 10,
        'temp_water_out':
            config.PLC.temp_water_out_offset +
            beck.get_node(config.PLC.Node.TEMP_WATER_OUT).get_value() / 10
    }

    return temp_values


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
        'flow_value': get_flow(beck=beck),
        'hygrometry': get_hygrometry(beck=beck)
    }

    return cooling_status


@core.beckhoff_autoconnect
def get_state(node, beck=None):
    """
    Open or Close the shutter depending on action_name

    :param node: bClose_Shutter or
    :return: position of flip_mirror
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
    :return: position of flip_mirror
    """

    if on:
        database.store('obs', {'temperature_log': f'Switching on {node}'})
    else:
        database.store('obs', {'temperature_log': f'Switching off {node}'})

    relay_switch = beck.get_node(node)
    relay_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(on, relay_switch.get_data_type_as_variant_type())))

    sleep(1)

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

    pump_temp = beck.get_node(config.PLC.Node.TEMP_PUMP).get_value() / 100

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

    # Update db to make sure the latest data point is valid
    #database.store_records('monitoring', {'flow_value': get_flow_value(beck=beck)})

    data = database.get_time_since_state('monitoring', 'flow_value', '>=',
                                         flow_threshold)

    if data.get('since') is None:
        return 0

    return (kalao_time.now() - data['since']['timestamp']).total_seconds()


@core.beckhoff_autoconnect
def get_flow(beck=None):
    """
    Convenience function to query the value of the water flow from the flowmeter

    TODO: add rounding of returned value

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    flow_value = beck.get_node(config.PLC.Node.FLOWMETER).get_value()

    return flow_value


@core.beckhoff_autoconnect
def get_hygrometry(beck=None):
    """
    Convenience function to query the value of the water flow from the flowmeter

    TODO: add rounding of returned value

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    flow_value = beck.get_node(config.PLC.Node.HYGROMETER).get_value()

    return flow_value


def get_cooling_values(beck=None):

    cooling = {
        'cooling_flow_value': get_flow(beck=beck),
        'hygrometry': get_hygrometry(beck=beck),
        'temp_water_in': get_temperatures(beck=beck)['temp_water_in']
    }

    camera_temperature = camera.get_temperatures()

    cooling['fli_temp_HS'] = camera_temperature['heatsink']
    cooling['fli_temp_CCD'] = camera_temperature['ccd']

    return cooling
