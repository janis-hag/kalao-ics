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
from kalao.cacao import fake_data



def short():
    """
    Query short status of all KalAO devices

    :return: dictionary with all device short status
    """

    short_status = {
        'ccd_temp': 'ERROR',
        'emccd_temp': 'ERROR'
    }

    # Add status from PLC
    short_status.update(core.plc_status())

    return short_status

def cacao_streams(realData=True):
    if realData:
        return fake_data.fake_streams() # TODO
    else:
        return fake_data.fake_streams()

def cacao_measurements(realData=True):
    if realData:
        return fake_data.fake_measurements() # TODO
    else:
        return fake_data.fake_measurements()
