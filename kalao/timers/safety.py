#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : safety.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Timer to verify KalAO bench health (KalAO-ICS).
"""

import datetime
import time

import numpy as np

import schedule

from kalao import euler, ippower
from kalao.cacao import aocontrol, toolbox
from kalao.fli import camera
from kalao.plc import laser, shutter, temperature_control
from kalao.utils import database, kalao_time
from sequencer import system

import kalao_config as config
from kalao_enums import CameraServerStatus, IPPowerStatus, LoopStatus

fps_list = {}


def _get_elapsed_time_since_activity():
    latest_obs_entry_time = database.get_last_record_time('obs_log')

    if latest_obs_entry_time is not None:
        return (kalao_time.now() - latest_obs_entry_time.replace(
                tzinfo=datetime.timezone.utc)).total_seconds()
    else:
        return np.inf


def _check_shutteropen_inactive():
    """
    Verify for how long the shutter is open and there is not observing activity.
    Close the shutter if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    # if switch_time long and no activity for given time close shutter
    # TODO ADD if tracking status IDLE, close

    if shutter.position() == 'OPEN':
        message = 'Closing shutter due to inactivity timeout'
        system.print_and_log(message)
        shutter.log(message)
        shutter.shutter_close()

    return 0


def _check_dm_inactive():
    """
    Verify for how long there is not observing activity.
    Turn off DM if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    bmc_display_fps = toolbox.open_fps_once('bmc_display-01', fps_list)

    if euler.sun_elevation() > config.Timers.dm_sun_min_elevation and (
            (bmc_display_fps is not None and bmc_display_fps.run_runs()) or
            ippower.ippower_status(
                    config.IPPower.Port.BMC_DM) == IPPowerStatus.ON):
        message = 'Turning off DM due to inactivity timeout'
        system.print_and_log(message)

        aocontrol.turn_dm_off()

    return 0


def _check_wfs_inactive():
    """
    Verify for how long there is not observing activity.
    Set EM gain to 1 if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    # TODO: check also EMGAIN keyword in nuvu_stream

    nuvu_acquire_fps = toolbox.open_fps_once('nuvu_acquire-1', fps_list)

    if nuvu_acquire_fps is not None and nuvu_acquire_fps.get_param(
            'emgain') > 1:

        message = 'Turning off EM gain due to inactivity timeout'
        system.print_and_log(message)

        aocontrol.emgain_off()
        aocontrol.set_exptime(0)

    return 0


def _check_loops_inactive():
    """
    Verify for how long there is not observing activity.
    Open loops in case of inactivity

    :return:
    """

    if aocontrol.check_loops() != LoopStatus.ALL_LOOPS_OFF:
        message = 'Opening loops due to inactivity timeout'
        system.print_and_log(message)

        aocontrol.open_loops()

    return 0


def _check_laseron_inactive():
    """
    Verify for how long the laser is on and there is not observing activity.
    Turn off laser if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    if laser.status() != 'OFF':
        message = 'Turning off laser due to inactivity timeout'
        system.print_and_log(message)
        laser.log(message)
        laser.disable()

    return 0


def _check_bench_status():
    """
    Checks the status of multiple bench components.

    :return: 0
    """

    inactivity_time = _get_elapsed_time_since_activity()

    if inactivity_time > config.Timers.inactivity_timeout:
        _check_shutteropen_inactive()
        _check_laseron_inactive()
        _check_dm_inactive()
        _check_wfs_inactive()
        _check_loops_inactive()

    return 0


def _check_cooling_status():
    """
    Verify cooling health status. Namely, the cooling water flow, and the main temperatures.
    If any value is below threshold either issue a warning or shutdown bench depending on level.

    :return: 0
    """

    cooling_status = temperature_control.get_cooling_values()

    latest_log = database.get_last_record_value('obs_log', 'sequencer_log')

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


if __name__ == "__main__":
    schedule.every(config.Timers.temperature_update_interval).seconds.do(
            _check_cooling_status)
    schedule.every(config.Timers.bench_update_interval).seconds.do(
            _check_bench_status)

    while True:
        n = schedule.idle_seconds()

        if n is None:
             break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
