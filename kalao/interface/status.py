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

import datetime

from kalao.plc import core
from kalao.cacao import fake_data, telemetry

from kalao.utils import database, kalao_time


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
    # Unused function to be removed.
    if realData:
        return database.get_all_last_monitoring()
    else:
        return fake_data.fake_telemetry()


def telemetry_series(nb_points, realData=True):
    if realData:
        return database.get_telemetry(['pi_tip', 'pi_tilt'], nb_points)
    else:
        return fake_data.fake_telemetry_series()


def latest_obs_log_entry(realData=True):
    if realData:
        latest_record = database.get_latest_record('obs_log')
        if latest_record is None:
            formated_entry_text = 'Obs logs empty'
        else:
            time_string = latest_record['time_utc'].isoformat(timespec='milliseconds')
            key_name = list(latest_record.keys())[1]
            record_text = latest_record[list(latest_record.keys())[1]]

            formated_entry_text = str(time_string)+' '+str(key_name)+': '+str(record_text)

        return formated_entry_text
    else:
        return fake_data.fake_latest_obs_log_entry()


def kalao_status():
    # TODO return sequencer_status, alt/az offset, focus offset, remaining_esposure_time 0 if not yet started
    sequencer_status = database.get_data('obs_log', ['sequencer_status'], 1)['sequencer_status']['values']
    if not sequencer_status:
        # If the status is not set assume that the sequencer is doww
        sequencer_status = 'DOWN'
    else:
        sequencer_status = sequencer_status[0]
    # TODO get alt/az and focus offset from cacao.telemetry and add to string
    sequencer_status = sequencer_status+'/'+elapsed_exposure_time()

    status_string = '/status/'+sequencer_status

    return status_string


def elapsed_exposure_time():

    #last_command_time = database.get_data('obs_log', ['sequencer_command_received'], 1)['sequencer_command_received']['time_utc'][0].replace(tzinfo=datetime.timezone.utc)

    last_exposure_start = database.get_data('obs_log', ['fli_image_count'], 1)['fli_image_count']['time_utc'][0].replace(tzinfo=datetime.timezone.utc)
    last_exposure_end = database.get_data('obs_log', ['fli_log'], 1)['fli_log']['time_utc'][0].replace(tzinfo=datetime.timezone.utc)

    if last_exposure_start > last_exposure_end:
        # An exposure is running
        elapsed_time = (kalao_time.now()-last_exposure_start).total_seconds()
    else:
        elapsed_time = 0

    return elapsed_time
