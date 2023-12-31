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

from kalao.utils import database, kalao_time
from kalao.plc import core
from kalao.fli import camera
from sequencer import system

import datetime
from opcua import ua
from time import sleep
import pandas as pd

from configparser import ConfigParser
from pathlib import Path
import os

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
# Read config file
parser = ConfigParser()
parser.read(config_path)

MINIMAL_FLOW = parser.getfloat('Cooling', 'MinimalFlow')
MAX_WATER_TEMP = parser.getfloat('Cooling', 'MaxWaterTemp')
MAX_HEATSINK_TEMP = parser.getfloat('Cooling', 'MaxHeatsinkTemp')
MAX_CCD_TEMP = parser.getfloat('Cooling', 'MaxCCDTemp')

pump_node = 'bRelayPump'
fan_node = 'bRelayFan'
heater_node = 'bWaterHeater'
flowmeter_node = 'iFlowmeter'


def get_temperatures(beck=None):
    """
    Query all the temperature sensors.

    :param beck: handle of the beckhoff connection
    :return: dictionary of temperatures
    """

    # Read calibrated temperature offset
    BENCHAIROFFSET = parser.getfloat('PLC', 'TempBenchAirOffset')
    BENCHBOARDOFFSET = parser.getfloat('PLC', 'TempBenchBoardOffset')
    WATERINOFFSET = parser.getfloat('PLC', 'TempWaterInOffset')
    WATEROUTOFFSET = parser.getfloat('PLC', 'TempWaterOutOffset')

    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    temp_values = {
            'temp_bench_air':
                    BENCHAIROFFSET +
                    beck.get_node('ns=4;s=MAIN.Temp_Bench_Air').get_value() /
                    10,
            'temp_bench_board':
                    BENCHBOARDOFFSET +
                    beck.get_node('ns=4;s=MAIN.Temp_Bench_Board').get_value() /
                    10,
            'temp_water_in':
                    WATERINOFFSET +
                    beck.get_node('ns=4;s=MAIN.Temp_Water_In').get_value() /
                    10,
            'temp_water_out':
                    WATEROUTOFFSET +
                    beck.get_node('ns=4;s=MAIN.Temp_Water_Out').get_value() /
                    10
    }

    if disconnect_on_exit:
        beck.disconnect()

    return temp_values


def get_cooling_status(beck=None):
    """
    Query status of the cooling system.

    :param beck: handle of the beckhoff connection
    :return:
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    cooling_status = {
            'pump_status': pump_status(beck),
            'pump_temp': pump_temperature(beck),
            'heater_status': heater_status(beck),
            'fan_status': fan_status(beck),
            'flow_value': get_flow_value(beck)
    }

    if disconnect_on_exit:
        beck.disconnect()

    return cooling_status


def status(relay_name, beck=None):
    """
    Open or Close the shutter depending on action_name

    :param relay_name: bClose_Shutter or
    :return: position of flip_mirror
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    if beck.get_node("ns=4;s=MAIN." + relay_name).get_value():
        relay_status = 'ON'
    else:
        relay_status = 'OFF'

    if disconnect_on_exit:
        beck.disconnect()

    return relay_status


def switch(relay_name, action, beck=None):
    """
     Open or Close the shutter depending on action_name

    :param relay_name: bClose_Shutter or
    :return: position of flip_mirror
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    relay_switch = beck.get_node("ns = 4; s = MAIN." + relay_name)
    relay_switch.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(action,
                               relay_switch.get_data_type_as_variant_type())))

    sleep(1)

    relay_status = status(relay_name, beck=beck)

    if disconnect_on_exit:
        beck.disconnect()

    return relay_status


def pump_on(beck=None):
    """
    Convenience function to turn on the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """
    pump_switch_status = switch(pump_node, True, beck=beck)
    return pump_switch_status


def pump_off(beck=None):
    """
    Convenience function to turn off the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """
    pump_switch_status = switch(pump_node, False, beck=beck)
    return pump_switch_status


def pump_status(beck=None):
    """
    Convenience function to query the status of the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """

    return status(pump_node, beck=beck)


def pump_temperature(beck=None):
    """
    Convenience function to query the temperature of the pump

    :param beck: beck: handle to the beckhoff connection
    :return: temperature of the pump in degrees
    """

    beck, disconnect_on_exit = core.check_beck(beck)

    pump_temp = beck.get_node("ns=4; s=MAIN.Temp_Pump").get_value() / 100

    if disconnect_on_exit:
        beck.disconnect()

    return pump_temp


def heater_on(beck=None):
    """
    Convenience function to turn on the water heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """
    heater_switch_status = switch(heater_node, True, beck=beck)
    return heater_switch_status


def heater_off(beck=None):
    """
    Convenience function to turn off the water heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """
    heater_switch_status = switch(heater_node, False, beck=beck)
    return heater_switch_status


def heater_status(beck=None):
    """
    Convenience function to query the status of the water heater

    :param beck: handle to the beckhoff connection
    :return: status of the heater
    """

    return status(heater_node, beck=beck)


def fan_on(beck=None):
    """
    Convenience function to turn on the water fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """
    fan_switch_status = switch(fan_node, True, beck=beck)
    return fan_switch_status


def fan_off(beck=None):
    """
    Convenience function to turn off the water fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """
    fan_switch_status = switch(fan_node, False, beck=beck)
    return fan_switch_status


def fan_status(beck=None):
    """
    Convenience function to query the status of the water fan

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    return status(fan_node, beck=beck)


def get_flow_threshold_time(flow_threshold, beck=None):
    """
    Looks up the time when the tungsten lamp as last been put into current state (ON/OFF/ERROR)

    :return:  switch_time a datetime object
    """
    # Update db to make sure the latest data point is valid
    #database.store_monitoring({'flow_value': get_flow_value(beck=beck)})

    # Load flow log into dataframe
    df = pd.DataFrame(
            database.get_monitoring({'flow_value'}, 1500)['flow_value'])

    # Verify if at least one value is above threshold
    if (df['values'] > flow_threshold).any():
        # Search for last occurrence of current status
        switch_index = df[df['values'] > flow_threshold].first_valid_index() - 1
    else:
        switch_index = -9

    if switch_index == -1:
        # flow is back above threshold
        elapsed_time = 0
    else:

        if switch_index == -9:
            # If no valid value use the oldest available time as switch. May not be valid on day change.
            switch_time = df.iloc[-1]['time_utc']

        else:
            switch_time = df.loc[
                    df[df['values'] > flow_threshold].first_valid_index() -
                    1]['time_utc']

        elapsed_time = (kalao_time.now() - switch_time.replace(
                tzinfo=datetime.timezone.utc)).total_seconds()

    return elapsed_time


def get_flow_value(beck=None):
    """
    Convenience function to query the value of the water flow from the flowmeter

    TODO: add rounding of returned value

    :param beck: handle to the beckhoff connection
    :return: status of the fan
    """

    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    flow_value = beck.get_node("ns=4;s=MAIN." + flowmeter_node).get_value()

    if disconnect_on_exit:
        beck.disconnect()

    return flow_value


def get_cooling_values(beck=None):

    cooling = {
            'cooling_flow_value': get_flow_value(beck=beck),
            'temp_water_in': get_temperatures(beck=beck)['temp_water_in']
    }

    camera_temperature = camera.get_temperatures()

    if isinstance(camera_temperature, dict):
        cooling['camera_HS_temp'] = camera_temperature['fli_temp_heatsink']
        cooling['camera_CCD_temp'] = camera_temperature['fli_temp_CCD']
    else:
        cooling['camera_HS_temp'] = -999
        cooling['camera_CCD_temp'] = -999

    return cooling
