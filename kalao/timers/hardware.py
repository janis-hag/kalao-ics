#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : hardware.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Timer to verify KalAO bench health (KalAO-ICS).
"""
import threading
import time
from datetime import datetime, timezone
from functools import partial
from typing import Callable

import numpy as np

from kalao import database, euler, ippower, logger
from kalao.cacao import aocontrol, toolbox
from kalao.hardware import (adc, calibunit, cooling, dm, filterwheel,
                            flipmirror, laser, plc, shutter, tungsten, wfs)
from kalao.utils import background

import schedule
from opcua import Client

from kalao.definitions.enums import (IPPowerStatus, LaserState, LoopStatus,
                                     RelayState, ShutterState)

import config


def _get_elapsed_time_since_activity() -> float:
    latest_obs_entry_time = database.get_collection_last_update('obs')

    if latest_obs_entry_time is not None:
        return (datetime.now(timezone.utc) -
                latest_obs_entry_time).total_seconds()
    else:
        return np.inf


def _check_shutteropen_inactive() -> None:
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


def _check_laseron_inactive() -> None:
    """
    Verify for how long the laser is on and there is not observing activity.
    Turn off laser if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    if laser.get_state() != LaserState.OFF:
        logger.info('hardware_timer',
                    'Turning off laser due to inactivity timeout')
        laser.disable()


def _check_dm_inactive() -> None:
    """
    Verify for how long there is not observing activity.
    Turn off DM if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    bmc_display_fps = toolbox.get_fps(config.FPS.BMC)

    if euler.sun_elevation() > config.Hardware.dm_sun_min_elevation and (
        (bmc_display_fps is not None and bmc_display_fps.run_isrunning()) or
            ippower.status(config.IPPower.Port.DM) == IPPowerStatus.ON):
        logger.info('hardware_timer',
                    'Turning off DM due to inactivity timeout')

        dm.off()


def _check_wfs_inactive() -> None:
    """
    Verify for how long there is not observing activity.
    Set EM gain to 1 if inactivity is longer than the value set in kalao.config file.

    :return:
    """

    # TODO: check also EMGAIN keyword in nuvu_stream

    nuvu_acquire_fps = toolbox.get_fps(config.FPS.NUVU)

    if nuvu_acquire_fps is not None and nuvu_acquire_fps.get_param(
            'emgain') > 1:
        logger.info('hardware_timer',
                    'Turning off EM gain due to inactivity timeout')

        wfs.emgain_off()
        wfs.set_exptime(0)

    if wfs.acquisition_running():
        logger.info('hardware_timer',
                    'Stopping WFS acquisition due to inactivity timeout')

        wfs.stop_acquisition()


def _check_loops_inactive() -> None:
    """
    Verify for how long there is not observing activity.
    Open loops in case of inactivity

    :return:
    """

    if aocontrol.check_loops() != LoopStatus.ALL_LOOPS_OFF:
        logger.info('hardware_timer',
                    'Opening loops due to inactivity timeout')
        aocontrol.open_loops()


def _check_inactivity() -> None:
    """
    Checks the status of multiple bench components.

    :return: 0
    """

    inactivity_time = _get_elapsed_time_since_activity()

    if inactivity_time > config.Hardware.inactivity_timeout:
        _check_shutteropen_inactive()
        _check_laseron_inactive()
        _check_dm_inactive()
        _check_wfs_inactive()
        _check_loops_inactive()


def _check_cooling_status() -> None:
    """
    Verify cooling health status. Namely, the cooling coolant flow, and the main temperatures.
    If any value is below threshold either issue a warning or shutdown bench depending on level.

    :return: 0
    """

    min_coolant_temp = database.definitions['monitoring']['metadata'][
        'coolant_temp_in']['warn_range'][0] + config.Cooling.heating_margin
    unit = database.definitions['monitoring']['metadata']['coolant_temp_in'][
        'unit']
    coolant_temp = cooling.get_status()['coolant_temp_in']

    if coolant_temp < min_coolant_temp:
        if cooling.heater_status() != RelayState.ON:
            logger.info(
                'hardware_timer',
                f'Coolant temperature too low ({coolant_temp} {unit}), starting heater'
            )
            cooling.heater_on()

        if cooling.heatexchanger_fan_status() != RelayState.OFF:
            logger.info(
                'hardware_timer',
                f'Coolant temperature too low ({coolant_temp} {unit}), stopping heat exchanger fan'
            )
            cooling.heatexchanger_fan_off()

    elif coolant_temp > min_coolant_temp + config.Cooling.heating_hysteresis:
        if cooling.heater_status() != RelayState.OFF:
            logger.info(
                'hardware_timer',
                f'Coolant temperature high enough ({coolant_temp} {unit}), stopping heater'
            )
            cooling.heater_off()

        if cooling.heatexchanger_fan_status() != RelayState.ON:
            logger.info(
                'hardware_timer',
                f'Coolant temperature high enough ({coolant_temp} {unit}), starting heat exchanger fan'
            )
            cooling.heatexchanger_fan_on()


@plc.autoconnect
def _check_pump_temp(beck: Client = None) -> None:
    pump_temp = cooling.pump_temperature(beck=beck)
    pump_status = cooling.pump_status(beck=beck)

    if pump_temp > config.Cooling.max_pump_temperature and pump_status == RelayState.ON:
        logger.warn('hardware_timer', 'Pump overheating, shutting off')
        cooling.pump_off(beck=beck)

    elif pump_temp < config.Cooling.pump_restart_temp and pump_status == RelayState.OFF:
        logger.warn('hardware_timer', 'Pump cooled down, powering up')
        cooling.pump_on(beck=beck)


def _check_plc() -> None:
    logger.info('hardware_timer', 'Doing daily PLC housekeeping')

    func_list = [
        partial(calibunit.init, force_init=True),
        partial(adc.init, config.PLC.Node.ADC1, force_init=True),
        partial(adc.init, config.PLC.Node.ADC2, force_init=True),
        shutter.init,
        flipmirror.init,
        tungsten.init,
        laser.init,
        filterwheel.init,
    ]

    background.launch('hardware_timer', func_list)


if __name__ == '__main__':

    def run_threaded(job_func: Callable) -> None:
        job_thread = threading.Thread(target=job_func)
        job_thread.start()

    schedule.every(config.Hardware.cooling_check_interval).seconds.do(
        run_threaded, _check_cooling_status)
    schedule.every(config.Hardware.inactivity_check_interval).seconds.do(
        run_threaded, _check_inactivity)
    schedule.every(60).seconds.do(run_threaded, _check_pump_temp)
    schedule.every().day.at('15:00',
                            'America/Santiago').do(run_threaded, _check_plc)

    while True:
        n = schedule.idle_seconds()

        if n is None:
            break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
