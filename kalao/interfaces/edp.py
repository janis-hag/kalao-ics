#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : edp.py
# @Date : 2021-01-02-16-50
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
The status functions are used to reply to Euler control software status requests as well as generating
datasets specific for the KalAO flask graphic user interface (GUI).

"""

from datetime import datetime, timezone
from typing import Any

from kalao import database
from kalao.hardware import camera, tungsten

from kalao.definitions.enums import SequencerStatus

import config


def kalao_status() -> str:
    """
    Generate the string sequence to return to the Euler telescope software on status request.

    :return: status_string to send to the Euler telescope
    """

    sequencer_status = database.get_last('obs', 'sequencer_status')
    sequencer_status_value = sequencer_status.get('value')

    if not sequencer_status_value:
        # If the status is not set, assume that the sequencer is down
        status_string = '|status|ERROR|0|DOWN'
    elif sequencer_status_value == SequencerStatus.WAITING:
        status_string = f'|status|WAITING|path|{_last_filepath_archived()}'
    elif sequencer_status_value == SequencerStatus.ERROR:
        status_string = '|status|ERROR'
    elif sequencer_status_value == SequencerStatus.WAITLAMP:
        status_string = f'|status|BUSY|{get_elapsed_time(sequencer_status):.0f}'
    elif sequencer_status_value == SequencerStatus.EXP:
        exposure_status = camera.get_exposure_status()
        elapsed_time = exposure_status["exposure_time"] - exposure_status[
            "remaining_time"]
        requested_time = exposure_status["exposure_time"]
        status_string = f'|status|BUSY|elapsed_time|{elapsed_time:.0f}|requested_time|{requested_time:.0f}'
    else:
        status_string = f'|status|BUSY|elapsed_time|{get_elapsed_time(sequencer_status):.0f}|requested_time|{sequencer_status_value}'

    return status_string


def get_elapsed_time(sequencer_status: dict[str, Any]) -> float:
    """
    Get the elapsed time since the current operation has started.

    :param: sequencer_status
    :return: Time in seconds
    """

    sequencer_status_value = sequencer_status.get('value')
    sequencer_status_time = sequencer_status.get('timestamp')

    if sequencer_status_value == SequencerStatus.WAITLAMP:
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

        elapsed_time = expected_time - (datetime.now(timezone.utc) -
                                        sequencer_status_time).total_seconds()

    return elapsed_time


def _last_filepath_archived() -> str:
    """
    Query the file path of the last saved image in the KalAO-ICS mongo database.

    :return: Image file path (str)
    """

    return database.get_last_value('obs', 'camera_last_image_path')
