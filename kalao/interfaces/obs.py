#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : obs.py
# @Date : 2021-01-02-16-50
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
The status functions are used to reply to Euler control software status requests as well as generating
datasets specific for the KalAO flask graphic user interface (GUI).

"""

import datetime

from kalao.plc import tungsten
from kalao.utils import database, kalao_time

from kalao.definitions.enums import SequencerStatus

import config


def kalao_status():
    """
    Generate the string sequence to return to the Euler telescope software on status request.
    TODO return sequencer_status, alt/az offset, focus offset, remaining_exposure_time 0 if not yet started

    :return: status_string to send to the Euler telescope
    """

    sequencer_status = database.get_last('obs', 'sequencer_status')
    sequencer_status_value = sequencer_status.get('value')

    if not sequencer_status_value:
        # If the status is not set, assume that the sequencer is down
        status_string = '|status|ERROR|0|DOWN'
    elif sequencer_status_value == SequencerStatus.WAITING:
        status_string = f'|status|{sequencer_status_value}|path|{_last_filepath_archived()}'
    elif sequencer_status_value == SequencerStatus.ERROR:
        status_string = f'|status|{sequencer_status_value}'
    elif sequencer_status_value == SequencerStatus.WAITLAMP:
        status_string = f'|status|BUSY|{elapsed_time(sequencer_status):.0f}'
    elif sequencer_status_value == SequencerStatus.EXP:
        texp = database.get_last_value('obs', 'fli_texp')
        status_string = f'|status|BUSY|elapsed_time|{elapsed_time(sequencer_status):.0f}|requested_time|{texp:.0f}'
    else:
        #  TODO get alt/az and focus offset from cacao.telemetry and add to string
        status_string = f'|status|BUSY|elapsed_time|{elapsed_time(sequencer_status):.0f}|requested_time|{sequencer_status_value}'

    return status_string


def elapsed_time(sequencer_status):
    """
    Get the elapsed time since the current operation has started.

    :param: sequencer_status
    :return: Time in seconds
    """

    sequencer_status_value = sequencer_status.get('value')
    sequencer_status_time = sequencer_status.get('timestamp')

    if sequencer_status_value == SequencerStatus.EXP:
        elapsed_time = elapsed_exposure_seconds()

    elif sequencer_status_value == SequencerStatus.WAITLAMP:
        state, switch_time = tungsten.get_switch_time()
        elapsed_time = config.Tungsten.stabilisation_time - switch_time

    else:
        expected_time = 0

        if sequencer_status_value == SequencerStatus.INITIALISING:
            expected_time = config.SEQ.init_duration

        elif sequencer_status_value == SequencerStatus.SETUP:
            k_type = database.get_last_value('obs', 'sequencer_obs_type')

            if k_type in config.SEQ.timings:
                expected_time = config.SEQ.timings[k_type]

        elapsed_time = expected_time - (kalao_time.now() -
                                        sequencer_status_time).total_seconds()

    return elapsed_time


def elapsed_exposure_seconds():
    """
    Calculates the elapsed time since the current operation has started.

    :return: Elapsed time in seconds (int)
    """

    last_exposure_start = _last_exposure_start()
    last_exposure_end = _last_exposure_end()

    if last_exposure_start > last_exposure_end:
        # An exposure is running
        elapsed_time = (kalao_time.now() - last_exposure_start).total_seconds()
    else:
        elapsed_time = (last_exposure_end -
                        last_exposure_start).total_seconds()

    return elapsed_time


def _last_exposure_start():
    """
    Query the time of the last exposure start in the KalAO-ICS mongo database.

    :return: Time of exposure start (datetime)
    """

    timestamp = database.get_last_time('obs', 'fli_image_count')

    if timestamp is None:
        return datetime.fromtimestamp(0)
    else:
        return timestamp


def _last_exposure_end():
    """
    Query the time of the last exposure end in the KalAO-ICS mongo database.

    :return: Time of exposure end (datetime)
    """

    timestamp = database.get_last_time('obs', 'fli_temporary_image_path')

    if timestamp is None:
        return datetime.fromtimestamp(0)
    else:
        return timestamp


def _last_filepath_archived():
    """
    Query the file path of the last saved image in the KalAO-ICS mongo database.

    :return: Image file path (str)
    """

    return database.get_last_value('obs', 'fli_last_image_path')
