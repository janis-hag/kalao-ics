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
from opcua import Client, ua


def status(beck=None):
    """
    Query the status of the flip mirror.

    :return: complete status of flip mirror
    """

    status_dict = core.device_status('Flip.FlipMirror', beck=beck)

    return status_dict
