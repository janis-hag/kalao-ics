#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : camera.py
# @Date : 2021-08-02-10-16
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
camera.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import os
import sys
import time

from microscope.filterwheels import thorlabs

from kalao.utils import database
from sequencer import system

import kalao_config as config

# Create bidirect dict with filter id (str and int)

id_filter_dict = {}
for position, filter_name in enumerate(config.FilterWheel.position_list):
    id_filter_dict[position] = filter_name
    id_filter_dict[filter_name] = position

id_only_filter_dict = {}
for position, filter_name in enumerate(config.FilterWheel.position_list):
    id_only_filter_dict[filter_name] = position


def create_filter_id():
    return id_filter_dict


def get_filter_ids():
    return id_only_filter_dict


def set_position(filter_arg):
    for retry in range(config.FilterWheel.retries):
        try:
            if type(filter_arg) == int and filter_arg not in range(0, 6):
                database.store_obs_log({
                        'filterwheel_log':
                                f"Error: wrong filter id got ({filter_arg})"
                })
                return -1
            elif type(filter_arg) == str:
                filter_arg = filter_arg.lower()
                if filter_arg not in id_filter_dict.keys():
                    database.store_obs_log({
                            'filterwheel_log':
                                    f"Error: wrong filter name (got {filter_arg})"
                    })
                    return -1
                else:
                    filter_arg = id_filter_dict[filter_arg]

            fw = thorlabs.ThorlabsFilterWheel(
                    com=config.FilterWheel.device_port)

            # fw.enable()
            # time.sleep(config.FilterWheel.enable_wait)
            # fw.initialize()
            # time.sleep(config.FilterWheel.initialization_wait)

            fw.set_position(filter_arg)  # Same name of parent func ?
            time.sleep(config.FilterWheel.position_change_wait)

            position = fw.get_position()
            filter_name = id_filter_dict[position]

            if position == filter_arg:
                database.store_obs_log({
                        'filterwheel_status': id_filter_dict[filter_arg]
                })
                return position, filter_name
            else:
                database.store_obs_log({
                        'filterwheel_log':
                                "Error: filter position expected {}, but got {}"
                                .format(filter_arg, position)
                })
                return -1

        except thorlabs.serial.SerialException:
            database.store_obs_log({
                    'filterwheel_log':
                            f'WARNING: SerialException on filterwheel. Retrying ({retry+1}/{config.FilterWheel.retries}).'
            })
            time.sleep(config.FilterWheel.enable_wait)

    database.store_obs_log({
            'filterwheel_log': 'ERROR: Filterwheel failed too many time.'
    })
    return -1


def get_position(from_db=False):
    if from_db:
        filter_name = database.get_last_record_value('obs_log',
                                                     key='filterwheel_status')
        position = id_filter_dict[filter_name]
    else:
        for retry in range(config.FilterWheel.retries):
            try:
                fw = thorlabs.ThorlabsFilterWheel(
                        com=config.FilterWheel.device_port)
                position = fw.get_position()
                filter_name = id_filter_dict[position]

                return position, filter_name

            except thorlabs.serial.SerialException:
                database.store_obs_log({
                        'filterwheel_log':
                                f'WARNING: SerialException on filterwheel. Retrying ({retry+1}/{config.FilterWheel.retries}).'
                })
                time.sleep(config.FilterWheel.enable_wait)

    database.store_obs_log({
            'filterwheel_log': 'ERROR: Filterwheel failed too many time.'
    })
    return None, None


def init():
    for retry in range(config.FilterWheel.retries):
        try:
            fw = thorlabs.ThorlabsFilterWheel(
                    com=config.FilterWheel.device_port)
            fw.enable()
            time.sleep(config.FilterWheel.enable_wait)
            fw.initialize()
            time.sleep(config.FilterWheel.initialization_wait)

            database.store_obs_log({
                    'filterwheel_log': "Initialising filterwheel"
            })

            return 0

        except thorlabs.serial.SerialException:
            database.store_obs_log({
                    'filterwheel_log':
                            f'WARNING: SerialException on filterwheel. Retrying ({retry+1}/{config.FilterWheel.retries}).'
            })
            time.sleep(config.FilterWheel.enable_wait)

    database.store_obs_log({
            'filterwheel_log': 'ERROR: Filterwheel failed too many time.'
    })
    return -1
