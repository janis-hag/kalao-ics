#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : info.py
# @Date : 2021-01-02-16-50
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
The status functions are used to reply to Euler control software status requests as well as generating
datasets specific for the KalAO flask graphic user interface (GUI).

"""

import datetime

from kalao.cacao import fake_data, telemetry
from kalao.plc import core, tungsten
from kalao.utils import database, kalao_time

import kalao_config as config
from kalao_enums import SequencerStatus


def short():
    """
    Query short status of all KalAO devices

    :return: dictionary with all device short status
    """

    short_status = {'ccd_temp': 'ERROR', 'emccd_temp': 'ERROR'}

    # Add status from PLC
    short_status.update(core.plc_status())

    return short_status


def streams(realData=True):
    if realData:
        return telemetry.streams()
    else:
        return fake_data.fake_streams()


def telemetry_series(nb_points, realData=True):
    if realData:
        return database.get_telemetry(['pi_tip', 'pi_tilt'], nb_points)
    else:
        return fake_data.fake_telemetry_series()


def latest_obs_log_entry(realData=True):
    """
    Queries the latest entry in the *obs_log* mongo database,

    :param realData:
    :return: Text string with the latest entry
    """

    if realData:
        latest_record = database._get_data('obs_log')
        if latest_record is None:
            formatted_entry_text = 'Obs logs empty'
        else:
            key_name = list(latest_record.keys())[0]
            time_string = latest_record[key_name][0]['timestamp'].isoformat(
                    timespec='milliseconds')
            record_text = latest_record[key_name][0]['value']

            formatted_entry_text = str(time_string) + ' ' + str(
                    key_name) + ': ' + str(record_text)

        return formatted_entry_text
    else:
        return fake_data.fake_latest_obs_log_entry()


def kalao_status():
    """
    Generate the string sequence to return to the Euler telescope software on status request.
    TODO return sequencer_status, alt/az offset, focus offset, remaining_exposure_time 0 if not yet started

    :return: status_string to send to the Euler telescope
    """

    sequencer_status = database.get_last_record_value(
            'obs_log', 'sequencer_status')
    if not sequencer_status:
        # If the status is not set assume that the sequencer is down
        status_string = '/status/ERROR/0/DOWN'
    elif sequencer_status == SequencerStatus.WAITING:
        status_string = '|status|' + sequencer_status + '|path|' + _last_filepath_archived()
    elif sequencer_status == SequencerStatus.ERROR:
        status_string = '/status/' + sequencer_status
    elif sequencer_status == SequencerStatus.WAITLAMP:
        status_string = '|status|BUSY|' + elapsed_time(sequencer_status)
    elif sequencer_status == SequencerStatus.EXP:
        # sequencer_command_received = database.get_latest_record_value('obs_log', key='sequencer_command_received')
        # if sequencer_command_received['type'] == 'K_LMPFLT':
        texp = int(database.get_last_record_value('obs_log', key='fli_texp'))
        # if
        # texp = database.get_latest_record_value('obs_log', key='sequencer_command_received')['texp']
        status_string = '|status|BUSY|elapsed_time|' + elapsed_time(
                sequencer_status) + '|requested_time|' + str(texp)
    else:
        #  TODO get alt/az and focus offset from cacao.telemetry and add to string
        status_string = '|status|BUSY|elapsed_time|' + elapsed_time(
                sequencer_status) + '|requested_time|' + sequencer_status

    # status_string = '/status/'+sequencer_status

    return status_string


def elapsed_time(sequencer_status):
    """
    Get the elapsed time since the current operation has started.

    :param sequencer_status: INITIALISING/SETUP/WAITLAMP
    :return: Time in seconds (str)
    """

    if sequencer_status == SequencerStatus.INITIALISING:
        status_time = database.get_last_record_time(
                'obs_log',
                key='sequencer_status').replace(tzinfo=datetime.timezone.utc)

        return str(config.SEQ.init_duration -
                   (kalao_time.now() -
                    status_time).total_seconds()).split('.')[0]

    elif sequencer_status == SequencerStatus.SETUP:
        k_type = database.get_last_record_value(
                'obs_log', key='sequencer_command_received')['type'][2:]

        if k_type.upper() in config.SEQ.timings:
            setup_time = config.SEQ.timings[k_type.upper()]
        else:
            setup_time = 0

        status_time = database.get_last_record_time(
                'obs_log',
                key='sequencer_status').replace(tzinfo=datetime.timezone.utc)

        return str(setup_time - (kalao_time.now() -
                                 status_time).total_seconds()).split('.')[0]

    elif sequencer_status == SequencerStatus.WAITLAMP:
        return str(config.Tungsten.stabilisation_time -
                   tungsten.get_switch_time()).split('.')[0]

    else:
        return elapsed_exposure_seconds()


def elapsed_exposure_seconds():
    """
    Calculates the elapsed time since the current operation has started.

    :return: Elapsed time in seconds (int)
    """

    last_exposure_start = _last_exposure_start()
    last_exposure_end = database.get_last_record_time(
            'obs_log', key='fli_temporary_image_path').replace(
                    tzinfo=datetime.timezone.utc)

    if last_exposure_start > last_exposure_end:
        # An exposure is running
        elapsed_time = str((kalao_time.now() -
                            last_exposure_start).total_seconds()).split('.')[0]
    else:
        elapsed_time = str((last_exposure_end -
                            last_exposure_start).total_seconds()).split('.')[0]

    return elapsed_time


def _last_exposure_start():
    """
    Query the time of the last exposure start in the KalAO-ICS mongo database.

    :return: Time of exposure start (datetime)
    """

    return database.get_last_record_time(
            'obs_log',
            key='fli_image_count').replace(tzinfo=datetime.timezone.utc)


def _last_filepath_archived():
    """
    Query the file path of the last saved image in the KalAO-ICS mongo database.

    :return: Image file path (str)
    """

    return database.get_last_record_value('obs_log',
                                          key='fli_last_image_path')
