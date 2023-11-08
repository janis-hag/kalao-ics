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

import schedule

from kalao import euler
from kalao.cacao import telemetry
from kalao.fli import camera
from kalao.plc import adc, core, filterwheel
from kalao.rtc import device_status
from kalao.utils import database

import kalao_config as config
from kalao_enums import CameraServerStatus

shm_and_fps_cache = {}

def update_plc_monitoring():
    values = {}

    # get monitoring from plc and store
    plc_values, plc_text = core.plc_status()

    # Do not log status of disabled devices.
    for device_name in config.PLC.disabled:
        plc_values.pop(device_name)
        plc_text.pop(device_name)
    values.update(plc_values)

    # get RTC data and update
    rtc_temperatures = device_status.read_all()
    values.update(rtc_temperatures)

    # FLI science camera status
    try:
        filter_number, filter_name = filterwheel.get_position()
        filter_status = {
                'fli_filter_position': filter_number,
                'fli_filter_name': filter_name
        }
        values.update(filter_status)
    except Exception as e:
        print(e)

    fli_server_status = camera.check_server_status()
    values.update({'fli_status': str(fli_server_status)})
    if fli_server_status == CameraServerStatus.UP:
        fli_temperatures = camera.get_temperatures()
        values.update(fli_temperatures)

    # ADC
    adc_status = {'adc_angle': adc.get_angle()}
    values.update(adc_status)

    # Telescope
    telescope = euler.telescope_coord_altaz()
    telescope_status = {'tel_alt': telescope.alt.deg, 'tel_az': telescope.az.deg}
    values.update(telescope_status)

    if not values == {}:
        database.store_monitoring(values)


def update_telemetry():
    telemetry.telemetry_save(shm_and_fps_cache)


if __name__ == "__main__":
    # Get monitoring and cacao
    schedule.every(config.Database.telemetry_update_interval).seconds.do(
            update_telemetry)
    schedule.every(config.Database.PLC_monitoring_update_interval).seconds.do(
            update_plc_monitoring)

    while True:
        n = schedule.idle_seconds()

        if n is None:
             break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
