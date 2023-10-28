#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : database_updater.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
database_updater.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

from signal import SIGINT, SIGTERM
from sys import exit
from time import sleep
import schedule

from kalao import plc
from kalao.rtc import device_status
from kalao import fli
from kalao.utils import database
from kalao.cacao import telemetry

import kalao_config as config

stream_and_fps_list = {}


def update_plc_monitoring():
    values = {}

    # get monitoring from plc and store
    plc_values, plc_text = plc.core.plc_status()

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
        filter_number, filter_name = plc.filterwheel.get_position()
        filter_status = {
                'fli_filter_position': filter_number,
                'fli_filter_name': filter_name
        }
        values.update(filter_status)
    except Exception as e:
        print(e)

    fli_server_status = fli.camera.check_server_status()
    values.update({'fli_status': fli_server_status})
    if fli_server_status == 'OK':
        fli_temperatures = fli.camera.get_temperatures()
        values.update(fli_temperatures)

    if not values == {}:
        database.store_monitoring(values)


def update_telemetry():
    telemetry.telemetry_save(stream_and_fps_list)


if __name__ == "__main__":
    # Get monitoring and cacao
    schedule.every(config.Database.telemetry_update_interval).seconds.do(
            update_telemetry)
    schedule.every(config.Database.PLC_monitoring_update_interval).seconds.do(
            update_plc_monitoring)

    while True:
        schedule.run_pending()
        sleep(5)
