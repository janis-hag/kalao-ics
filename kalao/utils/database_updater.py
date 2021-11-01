#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : database_updater.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
database_updater.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from signal import signal, SIGINT, SIGTERM
from sys import exit
from time import sleep
import schedule

from kalao import cacao  #.telemetry
from kalao import plc
from kalao import rtc
from kalao import fli
from kalao.utils import database
from kalao.filterwheel import filter_control
from sequencer import system

from configparser import ConfigParser
from pathlib import Path
import os

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')

# Read config file
parser = ConfigParser()
parser.read(config_path)

PLC_Disabled = parser.get('PLC','Disabled').split(',')


def handler(signal_received, frame):
    # Handle any cleanup here
    if signal_received == SIGTERM:
        # Restarting using systemd framework
        print('\nSIGTERM received. Restarting.')
        system.database_service('RESTART')
    elif signal_received == SIGINT:
        print('\nSIGINT or CTRL-C detected. Exiting.')
        exit(0)



def update_plc_monitoring():
    values = {}

    # get monitoring from plc and store
    plc_values, plc_text = plc.core.plc_status()

    # Do not log status of disabled devices.
    if not PLC_Disabled == 'None':
        for device_name in PLC_Disabled:
            plc_values.pop(device_name)
            plc_text.pop(device_name)
    values.update(plc_values)

    # get RTC data and update
    rtc_temperatures = rtc.temperatures.read_all()
    values.update(rtc_temperatures)

    # FLI science camera status
    filter_number, filter_name = filter_control.get_position()
    filter_status = {'fli_filter_position': filter_number, 'fli_filter_name': filter_name}
    values.update(filter_status)

    fli_server_status = fli.control.check_server_status()
    if fli_server_status == 'OK':
        fli_status = {'fli_temp_CCD': fli.control.get_temperature(), 'fli_status': fli_server_status}
        values.update(fli_status)
    else:
        values.update({'fli_status': fli_server_status})

    if not values == {}:
        database.store_monitoring(values)


if __name__ == "__main__":
    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGTERM, handler)
    signal(SIGINT, handler)

    # Get monitoring and cacao
    # schedule.every(60).seconds.do(cacao.telemetry.telemetry_save())
    schedule.every(60).seconds.do(update_plc_monitoring)

    while (True):
        schedule.run_pending()
        sleep(5)
