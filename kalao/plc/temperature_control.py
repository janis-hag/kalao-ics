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

import datetime
from time import sleep

import pandas as pd

from kalao.fli import camera
from kalao.plc import core
from kalao.utils import database, kalao_time

from opcua import ua

import config

pump_node = 'bRelayPump'
fan_node = 'bRelayFan'
heater_node = 'bWaterHeater'
flowmeter_node = 'iFlowmeter'

print_name = {
    'bRelayPump': 'pump',
    'bRelayFan': 'fan',
    'bWaterHeater': 'heater',
}


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
            beck.get_node('ns=4;s=MAIN.Temp_Bench_Air').get_value() / 10,
        'temp_bench_board':
            config.PLC.temp_bench_board_offset +
            beck.get_node('ns=4;s=MAIN.Temp_Bench_Board').get_value() / 10,
        'temp_water_in':
            config.PLC.temp_water_in_offset +
            beck.get_node('ns=4;s=MAIN.Temp_Water_In').get_value() / 10,
        'temp_water_out':
            config.PLC.temp_water_out_offset +
            beck.get_node('ns=4;s=MAIN.Temp_Water_Out').get_value() / 10
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
        'pump_status': pump_status(beck),
        'pump_temp': pump_temperature(beck),
        'heater_status': heater_status(beck),
        'fan_status': fan_status(beck),
        'flow_value': get_flow_value(beck)
    }

    return cooling_status


@core.beckhoff_autoconnect
def plc_status(relay_name, beck=None):
    """
    Open or Close the shutter depending on action_name

    :param relay_name: bClose_Shutter or
    :return: position of flip_mirror
    """

    if beck.get_node("ns=4;s=MAIN." + relay_name).get_value():
        relay_status = 'ON'
    else:
        relay_status = 'OFF'

    return relay_status


@core.beckhoff_autoconnect
def switch(relay_name, on, beck=None):
    """
     Open or Close the shutter depending on action_name

    :param relay_name: bClose_Shutter or
    :return: position of flip_mirror
    """

    if on:
        database.store('obs', {
            'temperature_log': f'Switching on {print_name[relay_name]}'
        })
    else:
        database.store('obs', {
            'temperature_log': f'Switching off {print_name[relay_name]}'
        })

    relay_switch = beck.get_node("ns = 4; s = MAIN." + relay_name)
    relay_switch.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(on, relay_switch.get_data_type_as_variant_type())))

    sleep(1)

    relay_status = plc_status(relay_name, beck=beck)

    return relay_status


def pump_on(beck=None):
    """
    Convenience function to turn on the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """

    return switch(pump_node, True, beck=beck)


def pump_off(beck=None):
    """
    Convenience function to turn off the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """

    return switch(pump_node, False, beck=beck)


def pump_status(beck=None):
    """
    Convenience function to query the status of the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """

    return plc_status(pump_node, beck=beck)


@core.beckhoff_autoconnect
def pump_temperature(beck=None):
    """
    Convenience function to query the temperature of the pump

    :param beck: beck: handle to the beckhoff connection
    :return: temperature of the pump in degrees
    """

    pump_temp = beck.get_node("ns=4; s=MAIN.Temp_Pump").get_value() / 100

    return pump_temp


def heater_on(beck=None):
    """
    Convenience function to turn on the water heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """

    return switch(heater_node, True, beck=beck)


def heater_off(beck=None):
    """
    Convenience function to turn off the water heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """

    return switch(heater_node, False, beck=beck)


def heater_status(beck=None):
    """
    Convenience function to query the status of the water heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """

    return plc_status(heater_node, beck=beck)


def fan_on(beck=None):
    """
    Convenience function to turn on the water fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return switch(fan_node, True, beck=beck)


def fan_off(beck=None):
    """
    Convenience function to turn off the water fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return switch(fan_node, False, beck=beck)


def fan_status(beck=None):
    """
    Convenience function to query the status of the water fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return plc_status(fan_node, beck=beck)


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
def get_flow_value(beck=None):
    """
    Convenience function to query the value of the water flow from the flowmeter

    TODO: add rounding of returned value

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    flow_value = beck.get_node("ns=4;s=MAIN." + flowmeter_node).get_value()

    return flow_value


def get_cooling_values(beck=None):

    cooling = {
        'cooling_flow_value': get_flow_value(beck=beck),
        'temp_water_in': get_temperatures(beck=beck)['temp_water_in']
    }

    camera_temperature = camera.get_temperatures()

    if isinstance(camera_temperature, dict):
        cooling['fli_temp_HS'] = camera_temperature['fli_temp_HS']
        cooling['fli_temp_CCD'] = camera_temperature['fli_temp_CCD']
    else:
        cooling['fli_temp_HS'] = -999
        cooling['fli_temp_CCD'] = -999

    return cooling
