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

from kalao.common.enums import SequencerStatus

from kalao.ics import database, memory
from kalao.ics.hardware import camera, tungsten
from kalao.ics.sequencer import centering

import config


def kalao_status() -> str:
    """
    Generate the string sequence to return to the Euler telescope software on status request.

    :return: status_string to send to the Euler telescope
    """

    sequencer_mapping = memory.hmget(
        'sequencer', {
            'status': (str, SequencerStatus.UNKNOWN.value),
            'status_timestamp': (float, 0)
        })

    sequencer_status = sequencer_mapping['status']
    exposure_status = camera.get_exposure_status()

    if sequencer_status is None:
        # If the status is not set, assume that the sequencer is down
        status_string = '|status|ERROR|0|DOWN'

    elif sequencer_status == SequencerStatus.WAITING:
        last_filepath_archived = database.get_last_value(
            'obs', 'camera_image_path')
        status_string = f'|status|WAITING|path|{last_filepath_archived}'

    elif sequencer_status == SequencerStatus.ERROR:
        status_string = '|status|ERROR'

    elif sequencer_status == SequencerStatus.WAIT_LAMP:
        state, switch_time = tungsten.get_switch_time()
        status_string = f'|status|BUSY|elapsed_time|{switch_time:.0f}/{config.Tungsten.stabilisation_time:.0f}|requested_time|WAIT_LAMP'

    elif sequencer_status == SequencerStatus.FOCUSING:
        focusing_step = memory.hget('sequencer', 'expno', type=int, default=0)
        status_string = f'|status|BUSY|elapsed_time|STEP {focusing_step}/{config.Focusing.nexp}|requested_time|FOCUSING'

    elif sequencer_status == SequencerStatus.CENTERING:
        centering_manual_flag = centering.get_manual_centering_flag()
        if centering_manual_flag:
            status_string = '|status|BUSY|elapsed_time|MANUAL|requested_time|CENTERING'
        else:
            centering_step = memory.hget('sequencer', 'expno', type=int,
                                         default=0)
            status_string = f'|status|BUSY|elapsed_time|STEP {centering_step}|requested_time|CENTERING'

    elif sequencer_status == SequencerStatus.EXPOSING:
        elapsed_time = exposure_status['exposure_time'] - exposure_status[
            'remaining_time']
        exposure_time = exposure_status['exposure_time']
        status_string = f'|status|BUSY|elapsed_time|{elapsed_time:.0f}|requested_time|{exposure_time:.0f}'

    else:
        if exposure_status['remaining_time'] > 0:
            elapsed_time = exposure_status['exposure_time'] - exposure_status[
                'remaining_time']
            exposure_time = exposure_status['exposure_time']
            status_string = f'|status|BUSY|elapsed_time|{elapsed_time:.0f}/{exposure_time}|requested_time|{sequencer_status}'
        else:
            elapsed_time = datetime.now(timezone.utc).timestamp(
            ) - sequencer_mapping['status_timestamp']
            status_string = f'|status|BUSY|elapsed_time|{elapsed_time:.0f}|requested_time|{sequencer_status}'

    return status_string
