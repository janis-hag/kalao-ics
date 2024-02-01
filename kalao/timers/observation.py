#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : observation.py
# @Date : 2023-09-21-13-20
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Timer to do offloading and adc update
"""

import time

from kalao import euler
from kalao.cacao import aocontrol
from kalao.plc import adc
from kalao.utils import offsets

import schedule

from kalao.definitions.enums import LoopStatus

import config


def _update_adc(beck=None):
    if euler.telescope_on_kalao() and euler.telescope_tracking():
        adc.configure(beck=beck, skip_tracking_check=True)


def _offload_ttm():
    if aocontrol.check_loops() == LoopStatus.ALL_LOOPS_ON:
        offsets.offload_ttm_to_telescope()


if __name__ == "__main__":
    schedule.every(config.ADC.update_interval).seconds.do(_update_adc)
    schedule.every(config.TTM.offload_interval).seconds.do(_offload_ttm)

    while True:
        n = schedule.idle_seconds()

        if n is None:
            break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
