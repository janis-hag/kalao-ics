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


def monitoring(realData=True):
    if realData:
        return database.get_all_last_monitoring()
    else:
        return fake_data.fake_monitoring()


def monitoring_series(realData=True):
    if realData:
        # Will be database.get_monitoring(keys, nb_of_point)
        return fake_data.fake_monitoring_series() # TODO
    else:
        return fake_data.fake_monitoring_series()


def latest_obs_log_entry():
    latest_record = database.get_latest_record('obs_log')
    time_string = latest_record['time_utc'].isoformat(timespec='milliseconds')
    key_name = list(latest_record.keys())[1]
    record_text = latest_record[list(latest_record.keys())[1]]
    formated_entry_text = time_string+' '+key_name+': '+record_text

    return formated_entry_text

def pi_tip_til_series(realData=True):
    if not realData:
