#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : database_updater.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Watchdog to verify KalAO bench health

TODO verify nuvu maximum flux and decrease EM gain or close shutter if needed.
(KalAO-ICS).
"""

import datetime
from time import sleep
import schedule

from kalao.plc import temperature_control, shutter
from kalao.utils import database, kalao_time
from kalao.fli import camera
from sequencer import system

from configparser import ConfigParser
from pathlib import Path
import os

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')

# Read config file
parser = ConfigParser()
parser.read(config_path)

PLC_Disabled = parser.get('PLC', 'Disabled').split(',')
TemperatureUpdateInterval = parser.getint('Watchdog',
                                          'TemperatureUpdateInterval')
BenchUpdateInterval = parser.getint('Watchdog', 'BenchUpdateInterval')
OpenShutterTimeout = parser.getint('Watchdog', 'OpenShutterTimeout')
InactivityTimeout = parser.getint('Watchdog', 'InactivityTimeout')

MINIMAL_FLOW = parser.getfloat('Cooling', 'MinimalFlow')
MAX_WATER_TEMP = parser.getfloat('Cooling', 'MaxWaterTemp')
MAX_HEATSINK_TEMP = parser.getfloat('Cooling', 'MaxHeatsinkTemp')
MAX_CCD_TEMP = parser.getfloat('Cooling', 'MaxCCDTemp')


def _check_shutteropen_inactive():
    # if switch_time long and no activity for given time close shutter

    if shutter.position() == 'OPEN':
        latest_obs_entry_time = database.get_latest_record(
                'obs_log')['time_utc']

        elapsed_time_since_activity = (
                kalao_time.now() - latest_obs_entry_time.replace(
                        tzinfo=datetime.timezone.utc)).total_seconds()

        open_shutter_elapsed_time = shutter.get_switch_time()

        if open_shutter_elapsed_time > OpenShutterTimeout and elapsed_time_since_activity > InactivityTimeout:
            message = 'Closing shutter due to inactivity timeout'
            system.print_and_log(message)
            shutter.log(message)
            shutter.shutter_close()

    return 0


def _check_bench_status():
    _check_shutteropen_inactive()

    return 0


def _check_cooling_status():
    """
    Verify cooling health status. Namely the cooling water flow, and the main temperatures.
    If any value is below threshold either issue a warning or shutdown bench depending on level.

    :return:
    """
    cooling_status = temperature_control.get_cooling_status()

    if cooling_status['cooling_flow'] < MINIMAL_FLOW:
        system.print_and_log(
                f"Error: cooling flow  {cooling_status['cooling_flow']} below mininum {MINIMAL_FLOW}"
        )

        system.print_and_log(f"Camera emergency poweroff")

        camera.poweroff()

        return -1

    if cooling_status['temp_water_in'] > MAX_WATER_TEMP:
        system.print_and_log(
                f"Error: water_in temperature {cooling_status['temp_water_in']} below mininum {MINIMAL_FLOW}"
        )
        return -1

    # Check if camera returns temperatures
    if cooling_status['fli_temp_heatsink'] > MAX_HEATSINK_TEMP:
        system.print_and_log(
                f"Error: fli_temp_heatsink temperature {cooling_status['fli_temp_heatsink']} below mininum {MAX_HEATSINK_TEMP}"
        )
        return -1

    if cooling_status['fli_temp_CCD'] > MAX_CCD_TEMP:
        system.print_and_log(
                f"Error: fli_temp_CCD temperature {cooling_status['fli_temp_CCD']} below mininum {MAX_CCD_TEMP}"
        )
        return -1

    return 0


if __name__ == "__main__":

    schedule.every(TemperatureUpdateInterval).seconds.do(_check_cooling_status)
    schedule.every(BenchUpdateInterval).seconds.do(_check_bench_status)

    while True:
        schedule.run_pending()
        sleep(5)
