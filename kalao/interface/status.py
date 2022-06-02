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
import os
from configparser import ConfigParser
from pathlib import Path

from kalao.plc import core, tungsten
from kalao.cacao import fake_data, telemetry

from kalao.utils import database, kalao_time

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
# Read config file
parser = ConfigParser()
parser.read(config_path)

InitDuration = parser.getint('SEQ', 'InitDuration')
TungstenStabilisationTime = parser.getint('PLC', 'TungstenStabilisationTime')
SetupTime = parser.getint('FLI', 'SetupTime')


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
            formatted_entry_text = 'Obs logs empty'
        else:
            time_string = latest_record['time_utc'].isoformat(timespec='milliseconds')
            key_name = list(latest_record.keys())[1]
            record_text = latest_record[list(latest_record.keys())[1]]

            formatted_entry_text = str(time_string)+' '+str(key_name)+': '+str(record_text)

        return formatted_entry_text
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
    sequencer_status = sequencer_status+'/'+elapsed_time(sequencer_status)

    status_string = '/status/'+sequencer_status

    return status_string


def elapsed_time(sequencer_status):

    if sequencer_status == 'INITIALISING':
         status_time = database.get_latest_record('obs_log', key='sequencer_status')['time_utc'].replace(tzinfo=datetime.timezone.utc)
         #database.get_data('obs_log', ['sequencer_status'], 1)['sequencer_status']['time_utc'][0].replace(tzinfo=datetime.timezone.utc)
         return str(InitDuration - (kalao_time.now() - status_time).total_seconds()).split('.')[0]

    elif sequencer_status == 'SETUP':
        ktype = database.get_latest_record('obs_log', key='sequencer_command_received')['sequencer_command_received']['ktype'][2:]

        if ktype == 'DARK':
            SetupTime = parser.getint('Timings', 'DARKsetup')
        elif ktype == 'LMPFLT':
            SetupTime = parser.getint('Timings', 'LMPFLTsetup')
        else:
            SetupTime = 0


        status_time = database.get_latest_record('obs_log', key='sequencer_status')['time_utc'].replace(
            tzinfo=datetime.timezone.utc)

        return str(SetupTime - (kalao_time.now() - status_time)).split('.')[0]

    elif sequencer_status == 'WAITLAMP':
        return str(TungstenStabilisationTime -tungsten.get_switch_time()).split('.')[0]

    else:
        return elapsed_exposure_seconds()


def elapsed_exposure_seconds():

    #last_command_time = database.get_data('obs_log', ['sequencer_command_received'], 1)['sequencer_command_received']['time_utc'][0].replace(tzinfo=datetime.timezone.utc)

    last_exposure_start = _last_exposure_start()
    #last_exposure_end = database.get_data('obs_log', ['fli_log'], 1)['fli_log']['time_utc'][0].replace(tzinfo=datetime.timezone.utc)
    last_exposure_end = database.get_latest_record('obs_log', key='fli_temporary_image_path')['time_utc'].replace(tzinfo=datetime.timezone.utc)
    #database.get_data('obs_log', ['fli_temporary_image_path'], 1)['fli_temporary_image_path']['time_utc'][0].replace(tzinfo=datetime.timezone.utc)

    if last_exposure_start > last_exposure_end:
        # An exposure is running
        elapsed_time = str((kalao_time.now()-last_exposure_start).total_seconds()).split('.')[0]
    else:
        elapsed_time = str((last_exposure_end - last_exposure_start).total_seconds()).split('.')[0]

    return elapsed_time

def _last_exposure_start():
    #return database.get_data('obs_log', ['fli_image_count'], 1)['fli_image_count']['time_utc'][0].replace(tzinfo=datetime.timezone.utc)
    return database.get_latest_record('obs_log', key='fli_image_count')['time_utc'].replace(tzinfo=datetime.timezone.utc)