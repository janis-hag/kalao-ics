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
from kalao.cacao import aocontrol, toolbox
from kalao.plc import adc
from kalao.utils import offsets

import schedule
from opcua import Client

from kalao.definitions.enums import LoopStatus

import config


def _update_adc(beck: Client = None) -> None:
    dynconfig_fps = toolbox.open_fps_once(config.FPS.CONFIG)

    if dynconfig_fps is None:
        return

    if dynconfig_fps.get_param('adc_update') and euler.telescope_on_kalao(
    ) and euler.telescope_tracking():
        adc.configure(beck=beck, skip_tracking_check=True)


def _offload_ttm() -> None:
    dynconfig_fps = toolbox.open_fps_once(config.FPS.CONFIG)

    if dynconfig_fps is None:
        return

    if dynconfig_fps.get_param('ttm_offload') and aocontrol.check_loops(
    ) == LoopStatus.ALL_LOOPS_ON:
        offsets.offload_ttm_to_telescope()


if __name__ == '__main__':
    schedule.every(config.ADC.update_interval).seconds.do(_update_adc)
    schedule.every(config.TTM.offload_interval).seconds.do(_offload_ttm)

    while True:
        n = schedule.idle_seconds()

        if n is None:
            break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
