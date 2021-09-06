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

from signal import signal, SIGINT
from sys import exit
from time import sleep

from kalao import cacao  #.telemetry
from kalao import plc
from kalao import rtc
from kalao import fli
from kalao.utils import database

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
    print('\nSIGINT or CTRL-C detected. Exiting.')
    # TODO it should restart using systemd framework
    exit(0)


def update_plc_monitoring():
    values = {}

    # get monitoring from plc and store
    plc_values, plc_text = plc.core.plc_status()

    # Do not log status of disabled devices.
    if PLC_Disabled == 'None':
        for device_name in PLC_Disabled:
            plc_values.pop(device_name)
            plc_text.pop(device_name)
    values.update(plc_values)

    # get RTC data and update
    rtc_temperatures = rtc.temperatures.read_all()
    values.update(rtc_temperatures)

    # FLI science camera status
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
    signal(SIGINT, handler)

    counter = 0
    while (True):
        # Get monitoring and cacao
        #cacao.telemetry.telemetry_save()
        counter +=1
        sleep(10)

        if counter > 5:
            #TODO counter should be time based

            update_plc_monitoring()

            counter = 0
