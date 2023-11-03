#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : loop.py
# @Date : 2023-09-21-13-20
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Watchdog to do offloading and adc update

"""

from time import sleep

import schedule

from kalao import euler
from kalao.cacao import aocontrol
from kalao.plc import adc

import kalao_config as config
from kalao_enums import LoopStatus, TrackingStatus


def _update_adc(beck=None):
    if euler.telescope_tracking() == TrackingStatus.TRACKING:
        adc.configure(beck=beck)


def _offload_ttm():
    if aocontrol.check_loop() == LoopStatus.ALL_LOOPS_ON:
        aocontrol.tip_tilt_offload_ttm_to_telescope(
                port=config.T120.port_loop_watchdog)


if __name__ == "__main__":
    schedule.every(config.ADC.update_interval).seconds.do(_update_adc)
    schedule.every(config.TTM.offload_interval).seconds.do(_offload_ttm)

    while True:
        schedule.run_pending()
        sleep(5)
