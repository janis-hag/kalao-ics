#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : database_updater.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Watchdog to verify KalAO bench health (KalAO-ICS).
"""

import datetime
from time import sleep
import schedule

from kalao import ippower
from kalao.plc import temperature_control, shutter, laser
from kalao.utils import database, kalao_time
from kalao.cacao import aocontrol, toolbox
from kalao.fli import camera
from sequencer import system

from kalao_enums import IPPowerStatus, CameraServerStatus
import kalao_config as config

fps_list = {}


def _get_elapsed_time_since_activity():
    latest_obs_entry_time = database.get_latest_record('obs_log')['time_utc']

    return (kalao_time.now() - latest_obs_entry_time.replace(
            tzinfo=datetime.timezone.utc)).total_seconds()


def _check_shutteropen_inactive(inactivity_time):
    """
    Verify for how long the shutter is open and there is not observing activity.
    Close the shutter if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    # if switch_time long and no activity for given time close shutter
    # TODO ADD if tracking status IDLE, close

    if shutter.position() == 'OPEN':
        open_shutter_elapsed_time = shutter.get_switch_time()

        if open_shutter_elapsed_time > config.Watchdog.open_shutter_timeout and inactivity_time > config.Watchdog.inactivity_timeout:
            message = 'Closing shutter due to inactivity timeout'
            system.print_and_log(message)
            shutter.log(message)
            shutter.shutter_close()

    return 0


def _check_dm_inactive(inactivity_time):
    """
    Verify for how long there is not observing activity.
    Turn off DM if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    bmc_display_fps = toolbox.open_fps_once('bmc_display-01', fps_list)

    if (bmc_display_fps is not None and
                bmc_display_fps.RUNrunning) or ippower.ippower_status(
                        config.IPPower.Port.BMC_DM) == IPPowerStatus.ON:
        if inactivity_time > config.Watchdog.inactivity_timeout:
            message = 'Turning off DM due to inactivity timeout'
            system.print_and_log(message)

            aocontrol.turn_dm_off(fps_list)

    return 0


def _check_wfs_inactive(inactivity_time):
    """
    Verify for how long there is not observing activity.
    Set EM gain to 1 if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    # TODO: check also EMGAIN keyword in nuvu_stream

    nuvu_acquire_fps = toolbox.open_fps_once('nuvu_acquire-1', fps_list)

    if nuvu_acquire_fps is not None and nuvu_acquire_fps.get_param_value_int(
            '.emgain') > 1:
        if inactivity_time > config.Watchdog.inactivity_timeout:
            message = 'Turning off EM gain due to inactivity timeout'
            system.print_and_log(message)

            aocontrol.emgain_off()

    return 0


def _check_laseron_inactive(inactivity_time):
    """
    Verify for how long the laser is on and there is not observing activity.
    Turn off laser if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    # Turn off laser if intensity is at 0
    if laser.status() == 0:
        laser.disable()

    if not laser.status() == 'OFF':
        laser_on_elapsed_time = laser.get_switch_time()

        if laser_on_elapsed_time > config.Watchdog.laser_on_timeout and inactivity_time > config.Watchdog.inactivity_timeout:
            message = 'Turning off laser due to inactivity timeout'
            system.print_and_log(message)
            laser.log(message)
            laser.disable()

    return 0


def _check_bench_status():
    """
    Checks the status of bench components: shutter, laser, DM and WFS.

    :return: 0
    """

    inactivity_time = _get_elapsed_time_since_activity()
    _check_shutteropen_inactive(inactivity_time)
    _check_laseron_inactive(inactivity_time)
    _check_dm_inactive(inactivity_time)
    _check_wfs_inactive(inactivity_time)

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

    if cooling_status['cooling_flow_value'] < config.Cooling.minimal_flow:

        # Get time since flow is too low
        low_flow_time = temperature_control.get_flow_threshold_time(
                config.Cooling.minimal_flow)

        if low_flow_time > config.Cooling.flow_grace_time:
            # Verify how low the cooling is already below minimal value.

            message = f"ERROR: Cooling flow value {cooling_status['cooling_flow_value']} below minimum {config.Cooling.minimal_flow} for {low_flow_time} seconds."

            if not latest_log.startswith(message[:24]):
                system.print_and_log(message)

            # IPPower has been moved to DM driver
            #if camera.ippower_status() == 1:

            #    system.print_and_log(f"Camera emergency power-off")

            #    camera.poweroff()

            return -1
        else:
            message = f"WARNING: Cooling flow value {cooling_status['cooling_flow_value']} below minimum"
            if not latest_log.startswith(message[:24]):
                system.print_and_log(message)

    elif cooling_status['cooling_flow_value'] < config.Cooling.flow_warn:
        system.print_and_log(
                f"WARNING: Low cooling flow value {cooling_status['cooling_flow_value']}"
        )

    if cooling_status['temp_water_in'] > config.Cooling.max_water_temp:
        message = f"ERROR: water_in temperature {cooling_status['temp_water_in']} above maxiumum {config.Cooling.max_water_temp}"
        if not latest_log.startswith(message[:24]):
            system.print_and_log(message)
        return -1

    # Check camera temperatures
    if camera.check_server_status() == CameraServerStatus.UP:
        # Verify if camera is running
        if cooling_status['camera_HS_temp'] > config.Cooling.max_heatsink_temp:
            message = f"ERROR: camera_HS_temp temperature {cooling_status['camera_HS_temp']} above maximum {config.Cooling.max_heatsink_temp}"

            if not latest_log.startswith(message[:24]):
                system.print_and_log(message)
            return -1

        elif cooling_status[
                'camera_HS_temp'] > config.Cooling.heatsink_temp_warn:
            message = f"WARNING: camera_HS_temp temperature {cooling_status['camera_HS_temp']} above warning threshold {config.Cooling.heatsink_temp_warn}"
            if not latest_log.startswith(message[:24]):
                system.print_and_log(message)
            return -1

        if cooling_status['camera_CCD_temp'] > config.Cooling.max_CCD_temp:
            message = f"ERROR: camera_CCD_temp temperature {cooling_status['camera_CCD_temp']} above maximum {config.Cooling.max_CCD_temp}"
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

    schedule.every(config.Watchdog.temperature_update_interval).seconds.do(
            _check_cooling_status)
    schedule.every(config.Watchdog.bench_update_interval).seconds.do(
            _check_bench_status)

    while True:
        schedule.run_pending()
        sleep(5)
