#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : hardware.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Timer to verify KalAO bench health (KalAO-ICS).
"""

import time
from datetime import datetime, timezone

import numpy as np

from kalao import database, euler, ippower, logger
from kalao.cacao import aocontrol, toolbox
from kalao.plc import (adc, calibunit, core, flipmirror, laser, shutter,
                       temperature_control)

import schedule

from kalao.definitions.enums import (IPPowerStatus, LaserState, LoopStatus,
                                     RelayState, ShutterState)

import config


def _get_elapsed_time_since_activity():
    latest_obs_entry_time = database.get_last_time('obs')

    if latest_obs_entry_time is not None:
        return (datetime.now(timezone.utc) -
                latest_obs_entry_time).total_seconds()
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
        logger.info('hardware_timer',
                    'Closing shutter due to inactivity timeout')
        shutter.close()

    return 0


def _check_laseron_inactive():
    """
    Verify for how long the laser is on and there is not observing activity.
    Turn off laser if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    if laser.get_state() != LaserState.OFF:
        logger.info('hardware_timer',
                    'Turning off laser due to inactivity timeout')
        laser.disable()

    return 0


def _check_dm_inactive():
    """
    Verify for how long there is not observing activity.
    Turn off DM if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    bmc_display_fps = toolbox.open_fps_once(config.FPS.BMC)

    if euler.sun_elevation() > config.Timers.dm_sun_min_elevation and (
        (bmc_display_fps is not None and bmc_display_fps.run_runs()) or
            ippower.status(config.IPPower.Port.BMC_DM) == IPPowerStatus.ON):
        logger.info('hardware_timer',
                    'Turning off DM due to inactivity timeout')

        aocontrol.turn_dm_off()

    return 0


def _check_wfs_inactive():
    """
    Verify for how long there is not observing activity.
    Set EM gain to 1 if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    # TODO: check also EMGAIN keyword in nuvu_stream

    nuvu_acquire_fps = toolbox.open_fps_once(config.FPS.NUVU)

    if nuvu_acquire_fps is not None and nuvu_acquire_fps.get_param(
            'emgain') > 1:
        logger.info('hardware_timer',
                    'Turning off EM gain due to inactivity timeout')

        aocontrol.emgain_off()
        aocontrol.set_exptime(0)

    nuvu_raw_stream = toolbox.open_stream_once(config.Streams.NUVU_RAW)

    if nuvu_raw_stream is not None:
        maqtime = datetime.fromtimestamp(
            nuvu_raw_stream.get_keywords()['_MAQTIME'] / 1e6, tz=timezone.utc)
        if (datetime.now(timezone.utc) -
                maqtime).total_seconds() < config.WFS.acquisition_time_timeout:
            logger.info('hardware_timer',
                        'Stopping WFS acquisition due to inactivity timeout')

            aocontrol.stop_wfs_acquisition()

    return 0


def _check_loops_inactive():
    """
    Verify for how long there is not observing activity.
    Open loops in case of inactivity

    :return:
    """

    if aocontrol.check_loops() != LoopStatus.ALL_LOOPS_OFF:
        logger.info('hardware_timer',
                    'Opening loops due to inactivity timeout')
        aocontrol.open_loops()

    return 0


def _check_inactivity():
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

    min_water_temp = database.definitions['monitoring']['metadata'][
        'temp_water_in']['warn_range'][0]
    unit = database.definitions['monitoring']['metadata']['temp_water_in'][
        'unit']
    water_temp = temperature_control.get_temperatures()['temp_water_in']

    if water_temp < min_water_temp:
        if temperature_control.heater_status() != RelayState.ON:
            logger.info(
                'hardware_timer',
                f'Water temperature too low ({water_temp} {unit}), starting heater'
            )
            temperature_control.heater_on()

    elif water_temp > min_water_temp + config.Cooling.heater_hysteresis_temp:
        if temperature_control.heater_status() != RelayState.OFF:
            logger.info(
                'hardware_timer',
                f'Water temperature high enough ({water_temp} {unit}), stopping heater'
            )
            temperature_control.heater_off()

    return 0


@core.beckhoff_autoconnect
def _check_pump_temp(beck=None):
    pump_temp = temperature_control.pump_temperature(beck=beck)
    pump_status = temperature_control.pump_status(beck=beck)

    if pump_temp > config.Cooling.max_pump_temperature and pump_status == RelayState.ON:
        logger.warn('hardware_timer', 'Pump overheat, shutting off')
        temperature_control.pump_off(beck=beck)

    elif pump_temp < config.Cooling.pump_restart_temp and pump_status == RelayState.OFF:
        logger.warn('hardware_timer', 'Pump cooled down, powering up')
        temperature_control.pump_on(beck=beck)


@core.beckhoff_autoconnect
def _check_plc(beck=None):
    logger.info('hardware_timer', 'Doing daily PLC housekeeping')

    calibunit.init(force_init=True, beck=beck)
    adc.init(config.PLC.Node.ADC1, force_init=True, beck=beck)
    adc.init(config.PLC.Node.ADC2, force_init=True, beck=beck)

    state, switch_time = shutter.get_switch_time()
    if switch_time > 86400:
        shutter.close(beck=beck)
        shutter.open(beck=beck)
        shutter.close(beck=beck)

    state, switch_time = flipmirror.get_switch_time()
    if switch_time > 86400:
        flipmirror.down(beck=beck)
        flipmirror.up(beck=beck)
        flipmirror.down(beck=beck)


if __name__ == "__main__":
    schedule.every(
        config.Timers.cooling_check_interval).seconds.do(_check_cooling_status)
    schedule.every(
        config.Timers.inactivity_check_interval).seconds.do(_check_inactivity)
    schedule.every(60).seconds.do(_check_pump_temp)
    schedule.every().day.at('15:00', 'America/Santiago').do(_check_plc)

    while True:
        n = schedule.idle_seconds()

        if n is None:
            break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
