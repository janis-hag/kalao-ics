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

from kalao import cacao #.telemetry
from kalao import plc #.core
from kalao import rtc #.temperatures
from kalao import fli
from kalao.utils import database

def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected. Exiting.')
    # TODO it should restart using systemd framework
    exit(0)


if __name__ == "__main__":
    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, handler)

    while (True):
        sleep(10)
        # Get measurements from and cacao
        #cacao.telemetry.measurements_save()

        values = {}
        #get Measurements from plc and store
        plc_values, text = plc.core.plc_status()
        values.update(plc_values)

        # get RTC data and update
        rtc_temperatures = rtc.temperatures.read_all()
        values.update(rtc_temperatures)

        # FLI science camera temperature
        fli_temperatures = {'fli_temp_CCD': fli.control.get_temperature()}
        values.update(fli_temperatures)

        database.store_measurements(values)
