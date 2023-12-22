#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : safety.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Timer to verify KalAO bench health (KalAO-ICS).
"""

import time

import numpy as np

from kalao import euler, ippower
from kalao.cacao import aocontrol, toolbox
from kalao.fli import camera
from kalao.plc import (adc, calib_unit, flip_mirror, laser, shutter,
                       temperature_control)
from kalao.utils import database, kalao_time

import schedule

from kalao.definitions.enums import (CameraServerStatus, IPPowerStatus,
                                     LaserState, LoopStatus, RelayState,
                                     ShutterState)

import config

fps_list = {}


def _get_elapsed_time_since_activity():
    latest_obs_entry_time = database.get_last_time('obs')

    if latest_obs_entry_time is not None:
        return (kalao_time.now() - latest_obs_entry_time).total_seconds()
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

    if shutter.get_state() == ShutterState.OPEN:
        database.store('obs', {
            'safety_timer_log': 'Closing shutter due to inactivity timeout'
        })
        shutter.close()

    return 0


def _check_dm_inactive():
    """
    Verify for how long there is not observing activity.
    Turn off DM if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    bmc_display_fps = toolbox.open_fps_once(config.FPS.BMC, fps_list)

    if euler.sun_elevation() > config.Timers.dm_sun_min_elevation and (
        (bmc_display_fps is not None and bmc_display_fps.run_runs()) or
            ippower.status(config.IPPower.Port.BMC_DM) == IPPowerStatus.ON):
        database.store('obs', {
            'safety_timer_log': 'Turning off DM due to inactivity timeout'
        })

        aocontrol.turn_dm_off()

    return 0


def _check_wfs_inactive():
    """
    Verify for how long there is not observing activity.
    Set EM gain to 1 if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    # TODO: check also EMGAIN keyword in nuvu_stream

    nuvu_acquire_fps = toolbox.open_fps_once(config.FPS.NUVU, fps_list)

    if nuvu_acquire_fps is not None and nuvu_acquire_fps.get_param(
            'emgain') > 1:
        database.store('obs', {
            'safety_timer_log': 'Turning off EM gain due to inactivity timeout'
        })

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
        database.store('obs', {
            'safety_timer_log': 'Opening loops due to inactivity timeout'
        })
        aocontrol.open_loops()

    return 0


def _check_laseron_inactive():
    """
    Verify for how long the laser is on and there is not observing activity.
    Turn off laser if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    if laser.get_state() != LaserState.OFF:
        database.store('obs', {
            'safety_timer_log': 'Turning off laser due to inactivity timeout'
        })
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

    #TODO: no action done currently

    cooling_status = temperature_control.get_cooling_values()
    ret = 0

    # Check water flow
    if cooling_status['cooling_flow_value'] < config.Cooling.minimal_flow:
        # Get time since flow is too low
        low_flow_time = temperature_control.get_flow_threshold_time(
            config.Cooling.minimal_flow)

        if low_flow_time > config.Cooling.flow_grace_time:
            # Verify how low the cooling is already below minimal value.
            database.store(
                'obs', {
                    'safety_timer_log':
                        f'[ERROR] Cooling flow value {cooling_status["cooling_flow_value"]} below minimum {config.Cooling.minimal_flow} for {low_flow_time} seconds.'
                })
            ret = -1

        else:
            database.store(
                'obs', {
                    'safety_timer_log':
                        f'[WARNING] Cooling flow value {cooling_status["cooling_flow_value"]} below minimum'
                })
            ret = -1

    elif cooling_status['cooling_flow_value'] < config.Cooling.flow_warn:
        database.store(
            'obs', {
                'safety_timer_log':
                    f'[WARNING] Low cooling flow value {cooling_status["cooling_flow_value"]}'
            })
        ret = -1

    # Check water temperature
    if cooling_status['temp_water_in'] > config.Cooling.max_water_temp:
        database.store(
            'obs', {
                'safety_timer_log':
                    f'[ERROR] water_in temperature {cooling_status["temp_water_in"]} above maxiumum {config.Cooling.max_water_temp}'
            })
        ret = -1

    elif cooling_status['temp_water_in'] < config.Cooling.min_water_temp:
        database.store(
            'obs', {
                'safety_timer_log':
                    f'[ERROR] water_in temperature {cooling_status["temp_water_in"]} below minimum {config.Cooling.min_water_temp}'
            })

        if temperature_control.heater_status() != RelayState.ON:
            temperature_control.heater_on()

        ret = -1

    elif cooling_status['temp_water_in'] > config.Cooling.heater_off_temp:
        if temperature_control.heater_status() != RelayState.OFF:
            temperature_control.heater_off()

    # Check camera temperatures
    if camera.check_server_status() == CameraServerStatus.UP:
        # Verify if camera is running
        if cooling_status['fli_temp_HS'] > config.Cooling.max_HS_temp:
            database.store(
                'obs', {
                    'safety_timer_log':
                        f'[ERROR] fli_temp_HS temperature {cooling_status["fli_temp_HS"]} above maximum {config.Cooling.max_HS_temp}'
                })
            ret = -1

        elif cooling_status['fli_temp_HS'] > config.Cooling.HS_temp_warn:
            database.store(
                'obs', {
                    'safety_timer_log':
                        f'[WARNING] fli_temp_HS temperature {cooling_status["fli_temp_HS"]} above warning threshold {config.Cooling.HS_temp_warn}'
                })
            ret = -1

        if cooling_status['fli_temp_CCD'] > config.Cooling.max_CCD_temp:
            database.store(
                'obs', {
                    'safety_timer_log':
                        f'[ERROR] fli_temp_CCD temperature {cooling_status["fli_temp_CCD"]} above maximum {config.Cooling.max_CCD_temp}'
                })
            ret = -1

        elif cooling_status['fli_temp_CCD'] > config.Cooling.CCD_temp_warn:
            database.store(
                'obs', {
                    'safety_timer_log':
                        f'[WARNING] fli_temp_CCD temperature {cooling_status["fli_temp_CCD"]} above warning threshold {config.Cooling.CCD_temp_warn}'
                })
            ret = -1

    return ret


def _check_plc():
    database.store('obs', {'safety_timer_log': 'Doing PLC housekeeping'})

    calib_unit.init(force_init=True)
    adc.init(config.PLC.Node.ADC1, force_init=True)
    adc.init(config.PLC.Node.ADC2, force_init=True)

    state, switch_time = shutter.get_switch_time()
    if switch_time > 86400:
        shutter.close()
        shutter.open()
        shutter.close()

    state, switch_time = flip_mirror.get_switch_time()
    if switch_time > 86400:
        flip_mirror.down()
        flip_mirror.up()
        flip_mirror.down()


if __name__ == "__main__":
    schedule.every(config.Timers.temperature_check_interval).seconds.do(
        _check_cooling_status)
    schedule.every(
        config.Timers.bench_check_interval).seconds.do(_check_bench_status)
    schedule.every().day.at('15:00', 'America/Santiago').do(_check_plc)

    while True:
        n = schedule.idle_seconds()

        if n is None:
            break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
