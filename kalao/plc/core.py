#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : beck.py
# @Date : 2021-01-02-14-40
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
beck.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from . import shutter
from . import calib_unit
from . import flip_mirror
from . import laser
from . import tungsten
from . import adc
from . import temperature_control
from kalao.utils import database

from opcua import Client

from configparser import ConfigParser
from pathlib import Path
import os

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
# Read config file
parser = ConfigParser()
parser.read(config_path)

PLC_IP = parser.get('PLC', 'IP')
PLC_PORT = parser.getint('PLC', 'Port')

def connect(addr=PLC_IP, port=PLC_PORT):
    beck = Client("opc.tcp://%s:%d" % (addr, port))
    beck.connect()
    # root = beck.get_root_node()
    # objects = beck.get_objects_node()
    # child = objects.get_children()
    return beck


def lamps_off():

    laser_status = laser.disable()
    tungsten_status = tungsten.off()

    if tungsten_status == 'OFF' and laser_status == 'OFF':
        return 0
    else:
        database.store_obs_log({'tungsten_log': 'WARNING: Unknown return status: '+str(tungsten_status)})
        return 1


def disabled_device_list():
    # Read config file
    parser.read(config_path)

    PLC_Disabled = parser.get('PLC', 'Disabled').split(',')

    return PLC_Disabled


def plc_status(beck=None):
    """
    Query status of all PLC connected devices
    :return: device status dictionary
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = check_beck(beck)

    # TODO check if all initialised

    temps = temperature_control.get_temperatures(beck=beck)

    cooling_system = temperature_control.get_cooling_status(beck=beck)

    plc_status_values = {'shutter': shutter.position(beck=beck),
                         'flip_mirror': flip_mirror.position(beck=beck),
                         'calib_unit': calib_unit.status(beck=beck)['lrPosActual'],
                         'temp_bench_air': temps['temp_bench_air'],
                         'temp_bench_board': temps['temp_bench_board'],
                         'temp_water_in': temps['temp_water_in'],
                         'temp_water_out': temps['temp_water_out'],
                         'laser': laser.status(beck=beck),
                         'tungsten': tungsten.status(beck=beck)['sStatus'],
                         'adc1': adc.status(1)['lrPosActual'],
                         'adc2': adc.status(2)['lrPosActual'],
                         'pump_status': cooling_system['pump_status'],
                         'heater_status': cooling_system['heater_status'],
                         'fan_status': cooling_system['fan_status'],
                         'flow_value': cooling_system['flow_value']
                         }

    plc_status_text = {'shutter': shutter.status(beck=beck)['sErrorText'],
                       'flip_mirror': flip_mirror.status(beck=beck)['sErrorText'],
                       'calib_unit': calib_unit.status(beck=beck)['sStatus'],
                       'temp_bench_air': temps['temp_bench_air'],
                       'temp_bench_board': temps['temp_bench_board'],
                       'temp_water_in': temps['temp_water_in'],
                       'temp_water_out': temps['temp_water_out'],
                       'laser': laser.status(beck=beck),
                       'tungsten': tungsten.status(beck=beck)['sStatus'],
                       'adc1': adc.status(1)['sStatus'],
                       'adc2': adc.status(2)['sStatus'],
                       'pump_status': cooling_system['pump_status'],
                       'heater_status': cooling_system['heater_status'],
                       'fan_status': cooling_system['fan_status'],
                       'flow_value': cooling_system['flow_value']
                       }

    if disconnect_on_exit:
        beck.disconnect()

    return plc_status_values, plc_status_text


def device_status(node_path, beck=None):
    """
    Query the status of a PLC connected device based on its path

    :return: complete status of calibration unit
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = check_beck(beck)

    device_status_dict = dict(sStatus=beck.get_node("ns=4; s=MAIN." + node_path + ".stat.sStatus").get_value(),
                              sErrorText=beck.get_node("ns=4; s=MAIN." + node_path + ".stat.sErrorText").get_value(),
                              nErrorCode=beck.get_node("ns=4; s=MAIN." + node_path + ".stat.nErrorCode").get_value(),
                              lrVelActual=beck.get_node("ns=4; s=MAIN." + node_path + ".stat.lrVelActual").get_value(),
                              lrVelTarget=beck.get_node("ns=4; s=MAIN." + node_path + ".stat.lrVelTarget").get_value(),
                              lrPosActual=beck.get_node("ns=4; s=MAIN." + node_path + ".stat.lrPosActual").get_value(),
                              lrPosition=beck.get_node("ns=4; s=MAIN." + node_path + ".ctrl.lrPosition").get_value())

    if disconnect_on_exit:
        beck.disconnect()

    return device_status_dict


def database_update(beck=None):
    values, text = plc_status(beck=beck)
    database.store_monitoring(values)


def check_beck(beck):

    # Connect to OPCUA server
    if beck is None:
        disconnect_on_exit = True
        beck = connect()
    else:
        disconnect_on_exit = False

    return beck, disconnect_on_exit