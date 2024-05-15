#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : database.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
database.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import time
from datetime import datetime, timezone
from typing import Any

import numpy as np

from kalao import database, euler, ippower, logger
from kalao.cacao import telemetry
from kalao.hardware import camera, plc_utils
from kalao.rtc import gpu, sensors
from kalao.utils import kstring

import schedule

from kalao.definitions.enums import CameraServerStatus

import config


def _gather_for_monitoring() -> dict[str, Any]:
    monitoring_data = {}

    # get monitoring from plc and store
    plc_values = plc_utils.get_all_status()

    # Do not log status of disabled devices.
    for device_name in config.PLC.disabled:
        plc_values.pop(device_name)
    monitoring_data.update(plc_values)

    # Get RTC data
    rtc_sensors = sensors.status()
    monitoring_data.update(rtc_sensors)

    rtc_gpu = gpu.status()
    monitoring_data.update(rtc_gpu)

    # IPPower
    ippower_status = ippower.status_all()
    monitoring_data.update(ippower_status)

    # FLI science camera status
    camera_server_status = camera.check_server_status()
    monitoring_data.update({'camera_server_status': camera_server_status})

    if camera_server_status == CameraServerStatus.UP:
        camera_temperatures = camera.get_temperatures()
        camera_temperatures['camera_temp_ccd'] = camera_temperatures.pop('ccd')
        camera_temperatures['camera_temp_heatsink'] = camera_temperatures.pop(
            'heatsink')
        monitoring_data.update(camera_temperatures)

    # Telescope
    telescope = euler.telescope_coord_altaz()
    telescope_status = {
        'telescope_altitude': telescope.alt.deg,
        'telescope_azimut': telescope.az.deg
    }
    monitoring_data.update(telescope_status)

    return monitoring_data


def update_monitoring_db() -> None:
    last_update = database.get_collection_last_update('monitoring')
    if (datetime.now(timezone.utc) - last_update
        ).total_seconds() < config.Database.monitoring_min_update_interval:
        return

    # logger.info('database_timer', 'Updating monitoring database')

    monitoring_data = _gather_for_monitoring()

    for key, value in monitoring_data.items():
        check_range('monitoring', key, value,
                    database.definitions['monitoring']['metadata'][key])

    if monitoring_data != {}:
        database.store('monitoring', monitoring_data)


def update_telemetry_db() -> None:
    # logger.info('database_timer', 'Updating telemetry database')

    telemetry_data = telemetry.gather()

    for key, value in telemetry_data.items():
        check_range('telemetry', key, value,
                    database.definitions['telemetry']['metadata'][key])

    if telemetry_data != {}:
        database.store('telemetry', telemetry_data)


def check_range(collection_name: str, key: str, value: int | float,
                metadata: dict[str, Any]) -> None:
    if not isinstance(value, float) and not isinstance(value, int):
        return

    error_range = metadata.get('error_range', [np.nan, np.nan])
    warn_range = metadata.get('warn_range', [np.nan, np.nan])

    error_min = error_range[0]
    error_max = error_range[1]
    warn_min = warn_range[0]
    warn_max = warn_range[1]

    unit = kstring.get_unit_string(metadata)

    if value > error_max:
        logger_func = logger.error
        threshold = error_max
        operator = '>'
    elif value < error_min:
        logger_func = logger.error
        threshold = error_min
        operator = '<'
    elif value > warn_max:
        logger_func = logger.warn
        threshold = warn_max
        operator = '>'
    elif value < warn_min:
        logger_func = logger.warn
        threshold = warn_min
        operator = '<'
    else:
        logger_func = None
        threshold = None
        operator = None

    if logger_func is not None:
        if logger_func == logger.error:
            level = 'error'
        elif logger_func == logger.warn:
            level = 'warning'

        if operator == '>':
            verb = 'over'
        elif operator == '<':
            verb = 'under'

        data = database.get_time_since_state(collection_name, key, operator,
                                             threshold)

        if data.get('since') is None:
            since = 0
        else:
            since = (datetime.now(timezone.utc) -
                     data['since']['timestamp']).total_seconds()

        logger_func(
            'database_timer',
            f'{key} = {value}{unit} {verb} {level} threshold of {threshold}{unit} (since {since} s)'
        )


if __name__ == '__main__':
    # Get monitoring and cacao
    schedule.every(config.Database.telemetry_update_interval).seconds.do(
        update_telemetry_db)
    schedule.every(config.Database.monitoring_update_interval).seconds.do(
        update_monitoring_db)

    while True:
        n = schedule.idle_seconds()

        if n is None:
            break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
