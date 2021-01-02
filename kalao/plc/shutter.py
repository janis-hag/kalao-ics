#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : shutter.py
# @Date : 2021-01-02-15-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
shutter.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

import core
import numbers

def status():
    """
    Query the full status of the shutter.

    :return: complete status shutter
    """
    # Connect to OPCUA server
    beck = core.connect()

    beck.get_node("ns=4; s=MAIN.Shutter.stat.lrPosActual").get_value()
    beck.get_node("ns=4; s=MAIN.Shutter.stat.sStatus").get_value()
    beck.get_node("ns=4; s=MAIN.Shutter.stat.sErrorText").get_value()
    beck.get_node("ns=4; s=MAIN.Shutter.stat.nErrorCode").get_value()
    beck.get_node("ns=4; s=MAIN.Shutter.stat.lrVelActual").get_value()
    beck.get_node("ns=4; s=MAIN.Shutter.stat.lrVelTarget").get_value()

    beck.disconnect()

def short_status():
    """
    Query the single string status of the shutter.

    :return: single string status of shutter
    """
    # Connect to OPCUA server
    beck = core.connect()

    # Check error status
    error_code = beck.get_node("ns=4; s=MAIN.Shutter.stat.nErrorCode").get_value()
    if error_code != 0:
        #someting went wrong
        return beck.get_node("ns=4; s=MAIN.Shutter.stat.sStatus").get_value()

    # beck.get_node("ns=4; s=MAIN.Shutter.stat.lrPosActual").get_value()
    # beck.get_node("ns=4; s=MAIN.Shutter.stat.sStatus").get_value()
    # beck.get_node("ns=4; s=MAIN.Shutter.stat.sErrorText").get_value()
    # beck.get_node("ns=4; s=MAIN.Shutter.stat.lrVelActual").get_value()
    # beck.get_node("ns=4; s=MAIN.Shutter.stat.lrVelTarget").get_value()

    beck.disconnect()

def init():
    """
    Initialise the shutter.

    :return: status of shutter
    """
    # Connect to OPCUA server
    beck = core.connect()
    beck.disconnect()
    return status


def open():
    """
    Open the shutter.

    :return: status of shutter
    """
    # Connect to OPCUA server
    beck = core.connect()
    beck.disconnect()
    return status



def close():
    """
    Close the shutter.

    :return: status of shutter
    """
    # Connect to OPCUA server
    beck = core.connect()

    beck.disconnect()
    return status