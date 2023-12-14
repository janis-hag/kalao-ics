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

from kalao import euler, ippower
from kalao.cacao import telemetry
from kalao.fli import camera
from kalao.plc import plc_utils
from kalao.rtc import rtc_status
from kalao.utils import database, kalao_time

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

    # get RTC data and update
    rtc_temperatures = rtc_status.read_all_sensors()
    monitoring_data.update(rtc_temperatures)

    # IPPower
    ippower_status = ippower.status_all()
    monitoring_data.update(ippower_status)

    # FLI science camera status
    fli_server_status = camera.check_server_status()
    monitoring_data.update({'fli_server_status': fli_server_status})

    if fli_server_status == CameraServerStatus.UP:
        fli_temperatures = camera.get_temperatures()
        fli_temperatures['fli_temp_CCD'] = fli_temperatures.pop('ccd')
        fli_temperatures['fli_temp_HS'] = fli_temperatures.pop('heatsink')
        monitoring_data.update(fli_temperatures)

    if euler.telescope_tracking() == TrackingStatus.TRACKING:
        # Telescope
        telescope = euler.telescope_coord_altaz()
        telescope_status = {
            'tel_alt': telescope.alt.deg,
            'tel_az': telescope.az.deg
        }
        monitoring_data.update(telescope_status)

    return monitoring_data


def update_monitoring_db():
    last_update = database.get_collection_last_update('monitoring')
    if (kalao_time.now() - last_update
        ).total_seconds() < config.Database.monitoring_min_update_interval:
        return

    #database.store('obs',
    #               {'database_timer_log': 'Updating monitoring database'})

    monitoring_data = _gather_for_monitoring()

    if monitoring_data != {}:
        database.store('monitoring', monitoring_data)


def update_telemetry_db():
    #database.store('obs',
    #               {'database_timer_log': 'Updating telemetry database'})

    telemetry.save(shm_and_fps_cache)


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
