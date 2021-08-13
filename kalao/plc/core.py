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
from kalao.utils import database

from opcua import Client
#from opcua import ua

from configparser import ConfigParser
from pathlib import Path
import os


def connect(addr="192.168.1.140", port=4840):
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
        database.store_obs_log({'tungsten_log': 'WARNING: Unknown return status: '+str(tungsten_status) })
        return 1

def disabled_device_list():
    config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')

    # Read config file
    parser = ConfigParser()
    parser.read(config_path)

    PLC_Disabled = parser.get('PLC', 'Disabled').split(',')

    return PLC_Disabled

def plc_status():
    """
    Query status of all PLC connected devices
    :return: device status dictionary
    """

    # TODO check if all initialised

    temps = temperatures()

    plc_status_values = {'shutter': shutter.position(),
                         'flip_mirror': flip_mirror.position(),
                         'calib_unit': calib_unit.status()['lrPosActual'],
                         'temp_bench_air': temps['temp_bench_air'],
                         'temp_bench_board': temps['temp_bench_board'],
                         'temp_water_in': temps['temp_water_in'],
                         'temp_water_out': temps['temp_water_out'],
                         'laser': laser.status(),
                         'tungsten': tungsten.status()['sStatus'],
                         'adc1': adc.status(1)['lrPosActual'],
                         'adc2': adc.status(2)['lrPosActual']
                         }

    plc_status_text = {'shutter': shutter.status()['sErrorText'],
                       'flip_mirror': flip_mirror.status()['sErrorText'],
                       'calib_unit': calib_unit.status()['sStatus'],
                       'temp_bench_air': temps['temp_bench_air'],
                       'temp_bench_board': temps['temp_bench_board'],
                       'temp_water_in': temps['temp_water_in'],
                       'temp_water_out': temps['temp_water_out'],
                       'laser': laser.status(),
                       'tungsten': tungsten.status()['sStatus'],
                       'adc1': adc.status(1)['sStatus'],
                       'adc2': adc.status(2)['sStatus']
                       }


    return plc_status_values, plc_status_text


def device_status(node_path, beck=None):
    """
    Query the status of a PLC connected device based on its path

    :return: complete status of calibration unit
    """
    # Connect to OPCUA server
    if beck is None:
        disconnect_on_exit = True
        beck = connect()
    else:
        disconnect_on_exit = False

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

def database_update():
    values, text = plc_status()
    database.store_monitoring(values)


def temperatures(beck=None):
    """
    Query the current intensity of the laser

    :return: intensity of laser
    """
    # Connect to OPCUA server
    if beck is None:
        disconnect_on_exit = True
        beck = connect()
    else:
        disconnect_on_exit = False

    temp_values = {'temp_bench_air': beck.get_node('ns=4;s=MAIN.Temp_Bench_Air').get_value()/10,
              'temp_bench_board': beck.get_node('ns=4;s=MAIN.Temp_Bench_Board').get_value()/10,
              'temp_water_in': beck.get_node('ns=4;s=MAIN.Temp_Water_In').get_value()/10,
              'temp_water_out': beck.get_node('ns=4;s=MAIN.Temp_Water_Out').get_value()/10
              }

    if disconnect_on_exit:
        beck.disconnect()

    return temp_values
