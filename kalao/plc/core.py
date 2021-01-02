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


from opcua import Client, ua


def connect(addr="192.168.1.140", port=4840):
    beck = Client("opc.tcp://%s:%d"%(addr, port))
    beck.connect()
    root = beck.get_root_node()
    objects = beck.get_objects_node()
    child = objects.get_children()
    return beck


def browse_recursive(client):
    node = client.get_root_node()
    for childId in node.get_children():
        ch = client.get_node(childId)
        print(ch.get_node_class())
        if ch.get_node_class() == ua.NodeClass.Object:
            browse_recursive(ch)
        elif ch.get_node_class() == ua.NodeClass.Variable:
            try:
                print("{bn} has value {val}".format(
                        bn=ch.get_browse_name(),
                        val=str(ch.get_value())))
            except ua.uaerrors._auto.BadWaitingForInitialData:
                pass


def status():
    """
    Query status of all PLC connected devices
    :return: device status dictionary
    """
    plc_status = {
        'shutter' : 'ERROR',
        'flip_mirror' : 'ERROR',
        'calib_unit' : 'ERROR',
        'temp_1' : 'ERROR',
        'temp_2' : 'ERROR',
        'temp_3' : 'ERROR',
        'temp_4' : 'ERROR'
    }

    return plc_status


