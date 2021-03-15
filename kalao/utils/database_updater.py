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

from ..cacao import telemetry
from ..plc  import core
from ..rtc import temperatures
from signal import signal, SIGINT
from sys import exit
from time import sleep

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
        telemetry.measurements_save()
        #get Measurements from plc and store
        core.database_update()

        # get RTC data and update
        temperatures.database_update()
        #database.store_measurements(data)

