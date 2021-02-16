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
from kalao.utils import database

from opcua import Client, ua


def connect(addr="192.168.1.140", port=4840):
    beck = Client("opc.tcp://%s:%d" % (addr, port))
    beck.connect()
    # root = beck.get_root_node()
    # objects = beck.get_objects_node()
    # child = objects.get_children()
    return beck


# def browse_recursive(client):
#     node = client.get_root_node()
#     for childId in node.get_children():
#         ch = client.get_node(childId)
#         print(ch.get_node_class())
#         if ch.get_node_class() == ua.NodeClass.Object:
#             browse_recursive(ch)
#         elif ch.get_node_class() == ua.NodeClass.Variable:
#             try:
#                 print("{bn} has value {val}".format(
#                         bn=ch.get_browse_name(),
#                         val=str(ch.get_value())))
#             except ua.uaerrors._auto.BadWaitingForInitialData:
#                 pass


def plc_status():
    """
    Query status of all PLC connected devices
    :return: device status dictionary
    """

    plc_status_values = {
        'shutter': shutter.position(),
        'flip_mirror': flip_mirror.position(),
        'calib_unit': calib_unit.status()['lrPosActual'],
        'temp_bench': 'ERROR',
        'temp_enclosure': 'ERROR',
        'temp_water_in': 'ERROR',
        'temp_water_out': 'ERROR',
        'laser': 'ERROR',
        'tungsten': 'ERROR'
    }

    plc_status_text = {
        'shutter': shutter.status()['sErrorText'],
        'flip_mirror': flip_mirror.status()['sErrorText'],
        'calib_unit': calib_unit.status()['sStatus'],
        'temp_bench': 'ERROR',
        'temp_enclosure': 'ERROR',
        'temp_water_in': 'ERROR',
        'temp_water_out': 'ERROR',
        'laser': 'ERROR',
        'tungsten': 'ERROR'
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
    database.store_measurements(values)
