#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : status.py
# @Date : 2021-01-02-16-50
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
status.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from kalao.plc import core


def short():
    """
    Query short status of all KalAO devices

    :return: dictionary with all device short status
    """

    other_status = {
        'ccd_temp': 'ERROR',
        'emccd_temp': 'ERROR'
    }

    plc_status = core.status()

    short_status = plc_status | other_status

    return short_status
