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
from kalao.cacao import fake_data, telemetry

from kalao.utils import database

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

def streams(realData=True):
    if realData:
        return telemetry.streams()
    else:
        return fake_data.fake_streams()

def measurements(realData=True):
    if realData:
        return database.get_all_last_measurements()
    else:
        return fake_data.fake_measurements()

def measurements_series(realData=True):
    if realData:
        # Will be database.get_measurements(keys, nb_of_point)
        return fake_data.fake_measurements_series() # TODO
    else:
        return fake_data.fake_measurements_series()
