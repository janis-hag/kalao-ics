#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : loop_watchdog.py
# @Date : 2023-09-21-13-20
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Watchdog to do offloading and adc update

"""

from time import sleep
import schedule

from kalao.plc import adc
from kalao.cacao import aocontrol

from configparser import ConfigParser
from pathlib import Path
import os

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')

# Read config file
parser = ConfigParser()
parser.read(config_path)

ADCUpdateInterval = parser.getfloat('ADC', 'ADCUpdateInterval')
TTMOffloadInterval = parser.getfloat('AO', 'TTMOffloadInterval')


def _update_adc(beck=None):
    adc.config_adc(beck=beck)


def _offload_ttm(beck=None):
    aocontrol.tip_tilt_offload(beck=beck)


if __name__ == "__main__":

    schedule.every(ADCUpdateInterval).seconds.do(_update_adc)
    schedule.every(TTMOffloadInterval).seconds.do(_offload_ttm)

    while True:
        schedule.run_pending()
        sleep(5)
