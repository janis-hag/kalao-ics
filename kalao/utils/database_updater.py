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

from signal import SIGINT, SIGTERM
from sys import exit
from time import sleep
import schedule

from pyMilk.interfacing.isio_shmlib import SHM

from CacaoProcessTools import fps, FPS_status
from kalao import plc
from kalao.rtc import device_status
from kalao import fli
from kalao.utils import database
from sequencer import system
from kalao.cacao import telemetry

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
    if not PLC_Disabled[0] == 'None':
        for device_name in PLC_Disabled:
            plc_values.pop(device_name)
            plc_text.pop(device_name)
    values.update(plc_values)

    # get RTC data and update
    rtc_temperatures = device_status.read_all()
    values.update(rtc_temperatures)

    # FLI science camera status
    try:
        filter_number, filter_name = plc.filterwheel.get_position()
        filter_status = {'fli_filter_position': filter_number, 'fli_filter_name': filter_name}
        values.update(filter_status)
    except Exception as e:
        print(e)

    fli_server_status = fli.camera.check_server_status()
    if fli_server_status == 'OK':
        fli_temperatures = fli.camera.get_temperatures()
        values.update(fli_temperatures)
    else:
        values.update({'fli_status': fli_server_status})

    if not values == {}:
        database.store_monitoring(values)


def update_telemetry(stream_list):

    if stream_list['nuvu_stream'] is None:
        nuvu_exists, nuvu_stream_path = telemetry.check_stream("nuvu_raw")
        if nuvu_exists:
            stream_list['nuvu_stream'] = SHM("nuvu_raw")

    if stream_list['tt_stream'] is None:
        nuvu_exists, nuvu_stream_path = telemetry.check_stream("dm02disp")
        if nuvu_exists:
            stream_list['tt_stream'] = SHM("dm02disp")

    if stream_list['fps_slopes'] is None:
        shwfs_exists, shwfs_fps_path = telemetry.check_fps("shwfs_process")
        if shwfs_exists:
            stream_list['fps_slopes'] = fps("shwfs_process")

    telemetry.telemetry_save(stream_list)


if __name__ == "__main__":
    # Tell Python to run the handler() function when SIGINT is recieved
    # signal(SIGTERM, handler)
    # signal(SIGINT, handler)

    sl = {'nuvu_stream': None, 'tt_stream': None, 'fps_slopes': None)

    # Get monitoring and cacao
    schedule.every(10).seconds.do(telemetry.update_telemetry, stream_list=sl)
    schedule.every(60).seconds.do(update_plc_monitoring)

    while (True):
        schedule.run_pending()
        sleep(5)
