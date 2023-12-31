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

from kalao.plc import temperature_control, shutter, laser
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
FLOW_WARN = parser.getfloat('Cooling', 'FlowWarn')
FLOW_GRACE_TIME = parser.getfloat('Cooling', 'FlowGraceTime')
MAX_WATER_TEMP = parser.getfloat('Cooling', 'MaxWaterTemp')
MAX_HEATSINK_TEMP = parser.getfloat('Cooling', 'MaxHeatsinkTemp')
HEATSINK_TEMP_WARN = parser.getfloat('Cooling', 'HeatsinkTempWarn')
MAX_CCD_TEMP = parser.getfloat('Cooling', 'MaxCCDTemp')

# TODO switch EM gain off after inactivity


def _check_shutteropen_inactive():
    """
    Verify for how long the shutter is open and there is not observing activity.
    Close the shutter if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    # if switch_time long and no activity for given time close shutter
    # TODO ADD if tracking status IDLE, close

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


def _check_laseron_inactive():
    """
    Verify for how long the laser is on and there is not observing activity.
    Turn off laser if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    # Turn off laser if intensity is at 0
    if laser.status() == 0:
        laser.disable()

    if not laser.status() == 'OFF':
        latest_obs_entry_time = database.get_latest_record(
                'obs_log')['time_utc']

        elapsed_time_since_activity = (
                kalao_time.now() - latest_obs_entry_time.replace(
                        tzinfo=datetime.timezone.utc)).total_seconds()

        laser_on_elapsed_time = laser.get_switch_time()

        if laser_on_elapsed_time > OpenShutterTimeout and elapsed_time_since_activity > InactivityTimeout:
            message = 'Turning off laser due to inactivity timeout'
            system.print_and_log(message)
            laser.log(message)
            laser.disable()

    return 0


def _check_bench_status():
    """
    Checks the satus of bench components: shutter, and laser.
    If inactivity timeout is reached, the shutter is closed, and the laser is turned off.

    :return: 0
    """

    _check_shutteropen_inactive()
    _check_laseron_inactive()

    return 0


def _check_cooling_status():
    """
    Verify cooling health status. Namely, the cooling water flow, and the main temperatures.
    If any value is below threshold either issue a warning or shutdown bench depending on level.

    :return: 0
    """

    cooling_status = temperature_control.get_cooling_values()

    latest_log = database.get_latest_record('obs_log',
                                            'sequencer_log')['sequencer_log']

    if cooling_status['cooling_flow_value'] < MINIMAL_FLOW:

        # Get time since flow is too low
        low_flow_time = temperature_control.get_flow_threshold_time(
                MINIMAL_FLOW)

        if low_flow_time > FLOW_GRACE_TIME:
            # Verify how low the cooling is already below minimal value.

            message = f"ERROR: Cooling flow value {cooling_status['cooling_flow_value']} below minimum {MINIMAL_FLOW} for {low_flow_time} seconds."

            if not latest_log.startswith(message[:24]):
                system.print_and_log(message)

            if camera.ippower_status() == 1:

                system.print_and_log(f"Camera emergency power-off")

                camera.poweroff()

            return -1
        else:
            message = f"WARNING: Cooling flow value {cooling_status['cooling_flow_value']} below minimum"
            if not latest_log.startswith(message[:24]):
                system.print_and_log(message)

    elif cooling_status['cooling_flow_value'] < FLOW_WARN:
        system.print_and_log(
                f"WARNING: Low cooling flow value {cooling_status['cooling_flow_value']}"
        )

    if cooling_status['temp_water_in'] > MAX_WATER_TEMP:
        message = f"ERROR: water_in temperature {cooling_status['temp_water_in']} below minimum {MINIMAL_FLOW}"
        if not latest_log.startswith(message[:24]):
            system.print_and_log(message)
        return -1

    # Check camera temperatures
    if camera.check_server_status() == 'OK':
        # Verify if camera is running
        if cooling_status['camera_HS_temp'] > MAX_HEATSINK_TEMP:
            message = f"ERROR: camera_HS_temp temperature {cooling_status['camera_HS_temp']} above minimum {MAX_HEATSINK_TEMP}"

            if not latest_log.startswith(message[:24]):
                system.print_and_log(message)
            return -1

        elif cooling_status['camera_HS_temp'] > HEATSINK_TEMP_WARN:
            message = f"WARNING: camera_HS_temp temperature {cooling_status['camera_HS_temp']}"
            if not latest_log.startswith(message[:24]):
                system.print_and_log(message)
            return -1

        if cooling_status['camera_CCD_temp'] > MAX_CCD_TEMP:
            message = f"ERROR: camera_CCD_temp temperature {cooling_status['camera_CCD_temp']} below minimum {MAX_CCD_TEMP}"
            if not latest_log.startswith(message[:24]):
                system.print_and_log(message)

            return -1

    return 0


def initialise():
    """
    Restart the systemd service for the watchdog.

    :return:
    """
    system.watchdog_service('restart')

    return 0


if __name__ == "__main__":

    schedule.every(TemperatureUpdateInterval).seconds.do(_check_cooling_status)
    schedule.every(BenchUpdateInterval).seconds.do(_check_bench_status)

    while True:
        schedule.run_pending()
        sleep(5)
