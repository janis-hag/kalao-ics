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

from kalao.plc import core, temperature_control
from kalao.utils import database, kalao_time

from sequencer import system

from configparser import ConfigParser
from pathlib import Path
import os

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')

# Read config file
parser = ConfigParser()
parser.read(config_path)


def _check_pump_temp():
    beck, disconnect_on_exit = core.check_beck()
    pump_temp = beck.get_node("ns=4; s=MAIN.Temp_Pump").get_value() / 100

    pump_status = temperature_control.pump_status(beck)

    if pump_temp > 40 and pump_status == 'ON':
        temperature_control.pump_off(beck)
        system.print_and_log("WARNING: Pump overheat, shutting off")

    elif pump_temp < 38 and pump_status == 'OFF':
        temperature_control.pump_on(beck)
        system.print_and_log("WARNING: Pump cooled down, powering up")

    if disconnect_on_exit:
        beck.disconnect()


if __name__ == "__main__":

    schedule.every(60).seconds.do(_check_pump_temp)

    while True:
        schedule.run_pending()
        sleep(5)
