#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : pump.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Timer to verify KalAO pump health

TODO verify nuvu maximum flux and decrease EM gain or close shutter if needed.
(KalAO-ICS).
"""

import time

import schedule

from kalao.plc import core, temperature_control
from sequencer import system

import kalao_config as config


def _check_pump_temp(beck=None):
    beck, disconnect_on_exit = core.check_beck(beck)
    pump_temp = temperature_control.pump_temperature(beck)

    pump_status = temperature_control.pump_status(beck)

    if pump_temp > config.Cooling.max_pump_temperature and pump_status == 'ON':
        temperature_control.pump_off(beck)
        system.print_and_log("WARNING: Pump overheat, shutting off")

    elif pump_temp < config.Cooling.pump_restart_temp and pump_status == 'OFF':
        temperature_control.pump_on(beck)
        system.print_and_log("WARNING: Pump cooled down, powering up")

    if disconnect_on_exit:
        beck.disconnect()


if __name__ == "__main__":
    schedule.every(60).seconds.do(_check_pump_temp)

    while True:
        n = schedule.idle_seconds()

        if n is None:
             break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
