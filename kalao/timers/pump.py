#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : pump.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Timer to verify KalAO pump health (KalAO-ICS).
"""

import time

from kalao.plc import core, temperature_control
from kalao.utils import database

import schedule

import config


@core.beckhoff_autoconnect
def _check_pump_temp(beck=None):
    pump_temp = temperature_control.pump_temperature(beck=beck)
    pump_status = temperature_control.pump_status(beck=beck)

    if pump_temp > config.Cooling.max_pump_temperature and pump_status == 'ON':
        database.store('obs', {
            'pump_timer_log': '[WARNING] Pump overheat, shutting off'
        })
        temperature_control.pump_off(beck=beck)

    elif pump_temp < config.Cooling.pump_restart_temp and pump_status == 'OFF':
        database.store('obs', {
            'pump_timer_log': '[WARNING] Pump cooled down, powering up'
        })
        temperature_control.pump_on(beck=beck)


if __name__ == "__main__":
    schedule.every(60).seconds.do(_check_pump_temp)

    while True:
        n = schedule.idle_seconds()

        if n is None:
            break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
