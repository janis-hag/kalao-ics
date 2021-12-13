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

from kalao.utils import database
from kalao.plc import core

from opcua import ua
from time import sleep

from configparser import ConfigParser
from pathlib import Path
import os

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
# Read config file
parser = ConfigParser()
parser.read(config_path)

pump_node = 'bRelayPump'
fan_node = 'bRelayFan'
heater_node = 'bWaterHeater'


def get_temperatures(beck=None):
    """
    Query the current intensity of the laser

    :return: intensity of laser
    """

    # Read calibrated temperature offset
    BENCHAIROFFSET = parser.getfloat('PLC', 'TempBenchAirOffset')
    BENCHBOARDOFFSET = parser.getfloat('PLC', 'TempBenchBoardOffset')
    WATERINOFFSET = parser.getfloat('PLC', 'TempWaterInOffset')
    WATEROUTOFFSET= parser.getfloat('PLC', 'TempWaterOutOffset')

    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    temp_values = {
        'temp_bench_air': BENCHAIROFFSET + beck.get_node('ns=4;s=MAIN.Temp_Bench_Air').get_value()/10,
        'temp_bench_board': BENCHBOARDOFFSET + beck.get_node('ns=4;s=MAIN.Temp_Bench_Board').get_value()/10,
        'temp_water_in': WATERINOFFSET + beck.get_node('ns=4;s=MAIN.Temp_Water_In').get_value()/10,
        'temp_water_out': WATEROUTOFFSET + beck.get_node('ns=4;s=MAIN.Temp_Water_Out').get_value()/10
        }

    if disconnect_on_exit:
        beck.disconnect()

    return temp_values


def pump_on(beck=None):
    """
    Convenience function to turn on the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """
    pump_status = switch(pump_node, True, beck=beck)
    return pump_status


def pump_off(beck=None):
    """
    Convenience function to turn off the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """
    pump_status = switch(pump_node, False, beck=beck)
    return pump_status


def pump_status(beck=None):
    """
    Convenience function to query the status of the water pump

    :param beck: handle to the beckhoff connection
    :return: status of the pump
    """

    return status(pump_node, beck=beck)


def status(relay_name, beck=None):
    """
    Open or Close the shutter depending on action_name

    :param action_name: bClose_Shutter or
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
        ua.AttributeIds.Value, ua.DataValue(ua.Variant(action, relay_switch.get_data_type_as_variant_type())))

    sleep(1)

    relay_status = status(relay_name, beck=beck)

    if disconnect_on_exit:
        beck.disconnect()

    return relay_status
