#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : observation.py
# @Date : 2023-09-21-13-20
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Timer to do offloading and adc update
"""
import threading
import time
from typing import Callable

import schedule

from kalao.common.enums import LoopStatus, SequencerStatus

from kalao.ics import euler, logger
from kalao.ics.cacao import aocontrol
from kalao.ics.hardware import adc, camera, ttm, wfs
from kalao.ics.sequencer import seq_utils

import config


def _update_adc() -> None:
    if euler.telescope_on_kalao() and euler.telescope_is_tracking():
        adc.configure()


def _offload_ttm() -> None:
    if aocontrol.check_loops() == LoopStatus.ALL_LOOPS_ON:
        ttm.offload_to_telescope()


def _check_ao() -> None:
    loops_status = aocontrol.check_loops()

    if LoopStatus.TTM_LOOP_ON in loops_status and LoopStatus.DM_LOOP_ON not in loops_status:
        logger.warn('observation_timer',
                    'Disabling TTM loop as DM loop is inactive')

        aocontrol.open_loop(config.AO.TTM_loop_number)

    elif LoopStatus.DM_LOOP_ON in loops_status:
        abort = False

        if not wfs.acquisition_running():
            logger.warn('observation_timer',
                        'Disabling loop(s) as WFS acquisition froze')
            abort = True

        elif not wfs.check_flux():
            logger.warn('observation_timer',
                        'Disabling loop(s) as flux is too low')
            abort = True

        if abort:
            seq_utils.set_sequencer_status(SequencerStatus.ABORTING_SOFTWARE)
            camera.cancel()
            aocontrol.open_loops()
            wfs.emgain_off()


if __name__ == '__main__':

    def run_threaded(job_func: Callable) -> None:
        job_thread = threading.Thread(target=job_func)
        job_thread.start()

    schedule.every(config.ADC.update_interval).seconds.do(
        run_threaded, _update_adc)
    schedule.every(config.TTM.offload_interval).seconds.do(
        run_threaded, _offload_ttm)
    schedule.every(config.AO.check_interval).seconds.do(
        run_threaded, _check_ao)

    while True:
        n = schedule.idle_seconds()

        if n is None:
            break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
