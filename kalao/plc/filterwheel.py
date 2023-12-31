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

import time

from kalao import database, logger

from microscope.filterwheels import thorlabs

from kalao.definitions.enums import FilterwheelStatus, ReturnCode

import config


def get_names_to_positions():
    return {n: p for p, n in enumerate(config.FilterWheel.position_list)}


def translate_to_filter_position(filter):
    if type(filter) == int:
        if filter not in range(0, 6):
            logger.error('filterwheel',
                         f'Wrong filter position, (got {filter})')
            return FilterwheelStatus.ERROR_POSITION
        else:
            return filter
    elif type(filter) == str:
        filter = filter.lower()

        if filter not in config.FilterWheel.position_list:
            logger.error('filterwheel', f'Wrong filter name (got {filter})')
            return FilterwheelStatus.ERROR_POSITION
        else:
            return config.FilterWheel.position_list.index(filter)
    else:
        return FilterwheelStatus.ERROR_POSITION


def translate_to_filter_name(filter):
    if type(filter) == int:
        if filter not in range(0, 6):
            logger.error('filterwheel',
                         f'Wrong filter position, (got {filter})')
            return FilterwheelStatus.ERROR_NAME
        else:
            return config.FilterWheel.position_list[filter]
    elif type(filter) == str:
        filter = filter.lower()

        if filter not in config.FilterWheel.position_list:
            logger.error('filterwheel', f'Wrong filter name (got {filter})')
            return FilterwheelStatus.ERROR_NAME
        else:
            return filter
    else:
        return FilterwheelStatus.ERROR_NAME


def set_filter(filter):
    position = translate_to_filter_position(filter)
    name = translate_to_filter_name(filter)

    logger.info('filterwheel',
                f'Setting filter wheel position to {position} ({name})')

    for retry in range(config.FilterWheel.retries):
        try:
            if position == FilterwheelStatus.ERROR_POSITION:
                return _return_filter(FilterwheelStatus.ERROR_POSITION, filter)

            fw = thorlabs.ThorlabsFilterWheel(
                com=config.FilterWheel.device_port)

            fw.set_position(position)

            time.sleep(config.FilterWheel.position_change_wait)

            position_act = fw.get_position()
            name_act = translate_to_filter_name(position_act)

            if position_act == position:
                database.store(
                    'obs', {
                        'filterwheel_filter_name': name,
                        'filterwheel_filter_position': position
                    })
                return _return_filter(position, filter)
            else:
                database.store(
                    'obs', {
                        'filterwheel_filter_name': name_act,
                        'filterwheel_filter_position': position_act
                    })
                logger.error(
                    'filterwheel',
                    f'Filter position expected {position} ({name}), but got {position_act} ({name_act})'
                )
                return _return_filter(position_act, filter)

        except thorlabs.serial.SerialException:
            logger.warn(
                'filterwheel',
                f'SerialException on filter wheel. Retrying ({retry+1}/{config.FilterWheel.retries}).'
            )
            time.sleep(config.FilterWheel.retry_wait)

        except ValueError:
            logger.warn(
                'filterwheel',
                f'ValueError on filter wheel. Retrying ({retry + 1}/{config.FilterWheel.retries}).'
            )
            time.sleep(config.FilterWheel.retry_wait)

    logger.error('filterwheel', 'Filter wheel failed too many time.')
    return _return_filter(FilterwheelStatus.ERROR_POSITION, filter)


def get_filter(type=str, from_db=False):
    if from_db:
        name = database.get_last_value('obs', 'filterwheel_filter_name')
        return _return_filter(name, type)
    else:
        for retry in range(config.FilterWheel.retries):
            try:
                fw = thorlabs.ThorlabsFilterWheel(
                    com=config.FilterWheel.device_port)
                position = fw.get_position()

                return _return_filter(position, type)

            except thorlabs.serial.SerialException:
                logger.warn(
                    'filterwheel',
                    f'SerialException on filter wheel. Retrying ({retry+1}/{config.FilterWheel.retries}).'
                )
                time.sleep(config.FilterWheel.retry_wait)

            except ValueError:
                logger.warn(
                    'filterwheel',
                    f'ValueError on filter wheel. Retrying ({retry+1}/{config.FilterWheel.retries}).'
                )
                time.sleep(config.FilterWheel.retry_wait)

    logger.error('filterwheel', 'Filter wheel failed too many time.')
    return _return_filter(FilterwheelStatus.ERROR_POSITION, type)


def _return_filter(filter, return_type):
    if type(return_type) != type:
        return_type = type(return_type)

    if return_type == str:
        return translate_to_filter_name(filter)
    elif return_type == int:
        return translate_to_filter_position(filter)
    else:
        logger.error('filterwheel', f'Unknown return type ({return_type}).')
        return None


def init():
    logger.info('filterwheel', 'Initialising filter wheel')

    for retry in range(config.FilterWheel.retries):
        try:
            fw = thorlabs.ThorlabsFilterWheel(
                com=config.FilterWheel.device_port)
            fw.enable()
            time.sleep(config.FilterWheel.enable_wait)
            fw.initialize()
            time.sleep(config.FilterWheel.initialization_wait)

            logger.info('filterwheel', 'Filter wheel initialised')

            return ReturnCode.PLC_INIT_SUCCESS

        except thorlabs.serial.SerialException:
            logger.warn(
                'filterwheel',
                f'SerialException on filter wheel. Retrying ({retry+1}/{config.FilterWheel.retries}).'
            )
            time.sleep(config.FilterWheel.retry_wait)

        except ValueError:
            logger.warn(
                'filterwheel',
                f'ValueError on filter wheel. Retrying ({retry + 1}/{config.FilterWheel.retries}).'
            )
            time.sleep(config.FilterWheel.retry_wait)

    logger.error('filterwheel', 'Filter wheel failed too many time.')
    logger.error('filterwheel', 'Filter wheel initialisation failed')

    return ReturnCode.PLC_INIT_FAILED
