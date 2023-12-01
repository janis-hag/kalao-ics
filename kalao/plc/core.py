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
from functools import wraps

from opcua import Client

import config


def connect(addr=config.PLC.ip, port=config.PLC.port):
    beck = Client(f'opc.tcp://{addr}:{port}')
    beck.connect()
    # root = beck.get_root_node()
    # objects = beck.get_objects_node()
    # child = objects.get_children()
    return beck


def beckhoff_autoconnect(fun):
    @wraps(fun)
    def wrapper(*args, beck=None, **kwargs):
        if beck is None:
            disconnect_on_exit = True
            beck = connect()
        else:
            disconnect_on_exit = False

        ret = fun(*args, beck=beck, **kwargs)

        if disconnect_on_exit:
            beck.disconnect()

        return ret

    return wrapper


@beckhoff_autoconnect
def device_status(node_path, beck=None):
    """
    Query the status of a PLC connected device based on its path

    :return: complete status of calibration unit
    """

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

    return device_status_dict


def wait_loop(message, test, wait_time):
    print(f"{message} ", end='', flush=True)
    while test():
        print(".", end='', flush=True)
        time.sleep(wait_time)
    print(" DONE", flush=True)
