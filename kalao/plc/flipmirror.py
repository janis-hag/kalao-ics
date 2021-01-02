#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : flipmirror
# @Date : 2021-01-02-15-08
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
flipmirror.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from . import core
import numbers


def status():
    """
    Query the status of the flip mirror.

    :return: complete status of flip mirror
    """
    # Connect to OPCUA server
    beck = core.connect()

    beck.get_node("ns=4; s=MAIN.FlipMirror.stat.lrPosActual").get_value()
    beck.get_node("ns=4; s=MAIN.FlipMirror.stat.sStatus").get_value()
    beck.get_node("ns=4; s=MAIN.FlipMirror.stat.sErrorText").get_value()
    beck.get_node("ns=4; s=MAIN.FlipMirror.stat.nErrorCode").get_value()
    beck.get_node("ns=4; s=MAIN.FlipMirror.stat.lrVelActual").get_value()
    beck.get_node("ns=4; s=MAIN.FlipMirror.stat.lrVelTarget").get_value()

    beck.disconnect()
