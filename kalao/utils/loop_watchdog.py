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
from kalao.interface import status

import kalao_config as config


def _update_adc(beck=None):
    if status.loop_running():
        adc.config_adc(beck=beck)


def _offload_ttm(beck=None):
    if status.loop_running():
        aocontrol.tip_tilt_offload_ttm_to_telescope()


if __name__ == "__main__":
    #schedule.every(config.ADC.update_interval).seconds.do(_update_adc)
    schedule.every(config.TTM.offload_interval).seconds.do(_offload_ttm)

    while True:
        schedule.run_pending()
        sleep(5)
