#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : telmetry.py
# @Date : 2021-03-18-10-02
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg, Nathanael Restori
"""
The telemetry package contains the tools to store the Adaptive Optics telemetry of KalAO.

"""

from kalao.cacao import toolbox

import config


def gather(shm_and_fps_cache={}):
    telemetry_data = {}

    # Nuvu stream
    nuvu_raw_stream = toolbox.open_stream_once('nuvu_raw', shm_and_fps_cache)

    if nuvu_raw_stream is not None:  # and session:
        stream_keywords = nuvu_raw_stream.get_keywords()

        telemetry_data['nuvu_temp_ccd'] = stream_keywords['T_CCD']
        telemetry_data['nuvu_temp_controller'] = stream_keywords['T_CNTRLR']
        telemetry_data['nuvu_temp_powersupply'] = stream_keywords['T_PSU']
        telemetry_data['nuvu_temp_fpga'] = stream_keywords['T_FPGA']
        telemetry_data['nuvu_temp_heatsink'] = stream_keywords['T_HSINK']
        telemetry_data['nuvu_emgain'] = stream_keywords['EMGAIN']
        telemetry_data['nuvu_detgain'] = stream_keywords['DETGAIN']
        telemetry_data['nuvu_exposuretime'] = stream_keywords['EXPTIME']
        telemetry_data['nuvu_mframerate'] = stream_keywords['MFRATE']

    # Nuvu process

    nuvu_fps = toolbox.open_fps_once(config.FPS.NUVU, shm_and_fps_cache)

    if nuvu_fps is not None and nuvu_fps.run_runs():
        telemetry_data['nuvu_autogain_on'] = nuvu_fps.get_param('autogain_on')
        telemetry_data['nuvu_autogain_setting'] = nuvu_fps.get_param(
            'autogain_setting')

    # BMC process

    bmc_fps = toolbox.open_fps_once(config.FPS.BMC, shm_and_fps_cache)

    if bmc_fps is not None and bmc_fps.run_runs():
        telemetry_data['bmc_max_stroke'] = bmc_fps.get_param('max_stroke')
        telemetry_data['bmc_stroke_mode'] = bmc_fps.get_param('stroke_mode')

    # SHWFS process
    shwfs_fps = toolbox.open_fps_once(config.FPS.SHWFS, shm_and_fps_cache)

    if shwfs_fps is not None and shwfs_fps.run_runs():
        telemetry_data['shwfs_algorithm'] = shwfs_fps.get_param('algorithm')
        telemetry_data['shwfs_flux_subaperture_avg'] = shwfs_fps.get_param(
            'flux_subaperture_avg')
        telemetry_data[
            'shwfs_flux_subaperture_brightest'] = shwfs_fps.get_param(
                'flux_subaperture_brightest')
        telemetry_data['shwfs_residual'] = shwfs_fps.get_param('residual')

    # Tip/tilt stream
    tt_stream = toolbox.open_stream_once(config.Streams.TTM, shm_and_fps_cache)

    if tt_stream is not None:
        # Check turned off to prevent timeout. Data may be obsolete
        tt_data = tt_stream.get_data(check=False)

        telemetry_data['pi_tip'] = float(tt_data[0])
        telemetry_data['pi_tilt'] = float(tt_data[1])

    # DM loop process
    dmloop_fps = toolbox.open_fps_once(config.FPS.DMLOOP, shm_and_fps_cache)

    if dmloop_fps is not None and dmloop_fps.run_runs():
        telemetry_data['dmloop_gain'] = dmloop_fps.get_param('loopgain')
        telemetry_data['dmloop_mult'] = dmloop_fps.get_param('loopmult')
        telemetry_data['dmloop_on'] = dmloop_fps.get_param('loopON')

        if telemetry_data['dmloop_on'] is True:
            telemetry_data['dmloop_on'] = 'ON'
        elif telemetry_data['dmloop_on'] is False:
            telemetry_data['dmloop_on'] = 'OFF'

    # TTM loop process
    ttmloop_fps = toolbox.open_fps_once(config.FPS.TTMLOOP, shm_and_fps_cache)

    if ttmloop_fps is not None and ttmloop_fps.run_runs():
        telemetry_data['ttmloop_gain'] = ttmloop_fps.get_param('loopgain')
        telemetry_data['ttmloop_mult'] = ttmloop_fps.get_param('loopmult')
        telemetry_data['ttmloop_on'] = ttmloop_fps.get_param('loopON')

        if telemetry_data['ttmloop_on'] is True:
            telemetry_data['ttmloop_on'] = 'ON'
        elif telemetry_data['ttmloop_on'] is False:
            telemetry_data['ttmloop_on'] = 'OFF'

    return telemetry_data
