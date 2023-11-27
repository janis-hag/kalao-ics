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

import time

from kalao.plc import (adc, calib_unit, flip_mirror, laser, shutter,
                       temperature_control, tungsten)
from kalao.utils import database

from opcua import Client

import config


def connect(addr=config.PLC.ip, port=config.PLC.port):
    beck = Client(f'opc.tcp://{addr}:{port}')
    beck.connect()
    # root = beck.get_root_node()
    # objects = beck.get_objects_node()
    # child = objects.get_children()
    return beck


def lamps_off():
    """
    Turns the tungsten and laser lamp off.

    :return:
    """

    laser_status = laser.disable()
    tungsten_status = tungsten.off()

    if tungsten_status == 'OFF' and laser_status == 'OFF':
        return 0

    if tungsten_status != 'OFF':
        database.store('obs', {
            'tungsten_log': f'[WARNING] Tungsten lamp did not turn off'
        })

    if laser_status != 'OFF':
        database.store('obs',
                       {'laser_log': f'[WARNING] Laser lamp did not turn off'})

    return 1


def plc_status(beck=None):
    """
    Query status of all PLC connected devices
    :return: device status dictionary
    """

    beck, disconnect_on_exit = check_beck(beck)

    # TODO check if all initialised

    temps = temperature_control.get_temperatures(beck=beck)
    cooling_system = temperature_control.get_cooling_status(beck=beck)
    laser_s = laser.plc_status(beck=beck)

    plc_status_values = {
        'shutter_state': shutter.get_state(beck=beck),
        'flip_mirror_position': flip_mirror.get_position(beck=beck),
        'calib_unit_position': calib_unit.plc_status(beck=beck)['lrPosActual'],
        'temp_bench_air': temps['temp_bench_air'],
        'temp_bench_board': temps['temp_bench_board'],
        'temp_water_in': temps['temp_water_in'],
        'temp_water_out': temps['temp_water_out'],
        'laser_state': laser_s['Status'],
        'laser_power': laser_s['Current'],
        'tungsten_state': tungsten.plc_status(beck=beck)['sStatus'],
        'adc1_angle': adc.plc_status(1)['lrPosActual'],
        'adc2_angle': adc.plc_status(2)['lrPosActual'],
        'pump_status': cooling_system['pump_status'],
        'pump_temp': cooling_system['pump_temp'],
        'heater_status': cooling_system['heater_status'],
        'fan_status': cooling_system['fan_status'],
        'flow_value': cooling_system['flow_value']
    }

    if disconnect_on_exit:
        beck.disconnect()

    return plc_status_values


def device_status(node_path, beck=None):
    """
    Query the status of a PLC connected device based on its path

    :return: complete status of calibration unit
    """
    beck, disconnect_on_exit = check_beck(beck)

    device_status_dict = dict(
        sStatus=beck.get_node("ns=4; s=MAIN." + node_path +
                              ".stat.sStatus").get_value(),
        sErrorText=beck.get_node("ns=4; s=MAIN." + node_path +
                                 ".stat.sErrorText").get_value(),
        nErrorCode=beck.get_node("ns=4; s=MAIN." + node_path +
                                 ".stat.nErrorCode").get_value(),
        lrVelActual=beck.get_node("ns=4; s=MAIN." + node_path +
                                  ".stat.lrVelActual").get_value(),
        lrVelTarget=beck.get_node("ns=4; s=MAIN." + node_path +
                                  ".stat.lrVelTarget").get_value(),
        lrPosActual=beck.get_node("ns=4; s=MAIN." + node_path +
                                  ".stat.lrPosActual").get_value(),
        lrPosition=beck.get_node("ns=4; s=MAIN." + node_path +
                                 ".ctrl.lrPosition").get_value())

    if disconnect_on_exit:
        beck.disconnect()

    return device_status_dict


def check_beck(beck):
    if beck is None:
        disconnect_on_exit = True
        beck = connect()
    else:
        disconnect_on_exit = False

    return beck, disconnect_on_exit


def wait_loop(message, test, wait_time):
    print(f"{message} ", end='', flush=True)
    while test():
        print(".", end='', flush=True)
        time.sleep(wait_time)
    print(" DONE", flush=True)
