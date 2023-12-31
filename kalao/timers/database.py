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

import numpy as np

from kalao import database, euler, ippower, logger
from kalao.cacao import telemetry
from kalao.fli import camera
from kalao.plc import plc_utils
from kalao.rtc import gpu, sensors
from kalao.utils import kalao_string, kalao_time

import schedule

from kalao.definitions.enums import CameraServerStatus, TrackingStatus

import config

shm_and_fps_cache = {}


def _gather_for_monitoring():
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
    fli_server_status = camera.check_server_status()
    monitoring_data.update({'fli_server_status': fli_server_status})

    if fli_server_status == CameraServerStatus.UP:
        fli_temperatures = camera.get_temperatures()
        fli_temperatures['fli_temp_ccd'] = fli_temperatures.pop('ccd')
        fli_temperatures['fli_temp_heatsink'] = fli_temperatures.pop(
            'heatsink')
        monitoring_data.update(fli_temperatures)

    if euler.telescope_tracking() == TrackingStatus.TRACKING:
        # Telescope
        telescope = euler.telescope_coord_altaz()
        telescope_status = {
            'telescope_altitude': telescope.alt.deg,
            'telescope_azimut': telescope.az.deg
        }
        monitoring_data.update(telescope_status)

    return monitoring_data


def update_monitoring_db():
    last_update = database.get_collection_last_update('monitoring')
    if (kalao_time.now() - last_update
        ).total_seconds() < config.Database.monitoring_min_update_interval:
        return

    # logger.info('database_timer', 'Updating monitoring database')

    monitoring_data = _gather_for_monitoring()

    for key, value in monitoring_data.items():
        check_range(key, value,
                    database.definitions['monitoring']['metadata'][key])

    if monitoring_data != {}:
        database.store('monitoring', monitoring_data)


def update_telemetry_db():
    # logger.info('database_timer', 'Updating telemetry database')

    telemetry_data = telemetry.gather(shm_and_fps_cache)

    for key, value in telemetry_data.items():
        check_range(key, value,
                    database.definitions['telemetry']['metadata'][key])

    if telemetry_data != {}:
        database.store('telemetry', telemetry_data)


def check_range(key, value, metadata):
    if not isinstance(value, float) and not isinstance(value, int):
        return

    error_range = metadata.get('error_range', [np.nan, np.nan])
    warn_range = metadata.get('warn_range', [np.nan, np.nan])

    error_min = error_range[0]
    error_max = error_range[1]
    warn_min = warn_range[0]
    warn_max = warn_range[1]

    unit = kalao_string.get_unit_string(metadata)

    if value > error_max:
        logger.error(
            'database_timer',
            f'{key} = {value}{unit} above error threshold of {error_max}{unit}'
        )
    elif value < error_min:
        logger.error(
            'database_timer',
            f'{key} = {value}{unit} under error threshold of {error_min}{unit}'
        )
    elif value > warn_max:
        logger.warn(
            'database_timer',
            f'{key} = {value}{unit} above warning threshold of {warn_max}{unit}'
        )
    elif value < warn_min:
        logger.warn(
            'database_timer',
            f'{key} = {value}{unit} under warning threshold of {warn_min}{unit}'
        )


if __name__ == "__main__":
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
