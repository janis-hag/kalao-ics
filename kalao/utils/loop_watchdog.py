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

import config


def _update_adc(beck=None):
    adc.config_adc(beck=beck)


def _offload_ttm(beck=None):
    aocontrol.tip_tilt_offload(beck=beck)


if __name__ == "__main__":

    schedule.every(config.ADC.update_interval).seconds.do(_update_adc)
    schedule.every(config.TTM.offload_interval).seconds.do(_offload_ttm)

    while True:
        schedule.run_pending()
        sleep(5)
