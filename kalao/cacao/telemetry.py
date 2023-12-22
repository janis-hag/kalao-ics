#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : telmetry.py
# @Date : 2021-03-18-10-02
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg, Nathanael Restori
"""
The telemetry package contains the tools to store the Adaptive Optics telemetry of KalAO.

"""

import traceback

import numpy as np

from kalao.cacao import toolbox
from kalao.utils import database

import config

empty_stream = {
    "data": 0,
    "width": 0,
    "height": 0,
    "min": 0,
    "max": 0,
    "min_th": 0,
    "max_th": 0,
}


def _get_stream(name, min_value_th, max_value_th, shm_cache={}):
    """
    Get stream data, after having verified that the stream with that name exists.

    :param name: stream name
    :param min_value_th: theoretical minimal value in the stream
    :param max_value_th: theoretical maximal value in the stream
    :param shm_cache: streams cache
    :return: Dictionary with: data, width, height, min, max, min_th, max_th
    """

    stream_shm = toolbox.open_stream_once(name, shm_cache)

    if stream_shm is not None:
        try:
            data = stream_shm.get_data(check=False)

            if len(data.shape) == 1:
                # One dimensional stream
                width = 1
                height = data.shape[0]
            else:
                width = data.shape[1]
                height = data.shape[0]

            min_value = np.min(data)
            max_value = np.max(data)

            return {
                "data": data.flatten().tolist(),
                "width": width,
                "height": height,
                "min": float(min_value),
                "max": float(max_value),
                "min_th": min_value_th,
                "max_th": max_value_th,
            }
        except:
            print(traceback.format_exc())
            return empty_stream
    else:
        return empty_stream


def streams(shm_cache={}):
    """
    Provides all the streams needed for the KalAO GUI.

    :param shm_cache: Dictionary of open streams
    :return: dictionary with all the stream contents
    """

    stream_list = {}

    stream_list["nuvu_stream"] = _get_stream(name="nuvu_stream",
                                             min_value_th=0,
                                             max_value_th=2**16 - 1,
                                             shm_cache=shm_cache)

    stream_list["shwfs_slopes"] = _get_stream(name="shwfs_slopes",
                                              min_value_th=-2, max_value_th=2,
                                              shm_cache=shm_cache)

    stream_list["dm01disp"] = _get_stream(name="dm01disp", min_value_th=-1.75,
                                          max_value_th=1.75,
                                          shm_cache=shm_cache)

    stream_list["shwfs_slopes_flux"] = _get_stream(
        name="shwfs_slopes_flux", min_value_th=0, max_value_th=4 * (2**16 - 1),
        shm_cache=shm_cache)

    stream_list["aol1_mgainfact"] = _get_stream(name="aol1_mgainfact",
                                                min_value_th=0, max_value_th=1,
                                                shm_cache=shm_cache)

    streams["aol1_modeval"] = _get_stream(name="aol1_mgainfact",
                                          min_value_th=-1.75,
                                          max_value_th=1.75,
                                          shm_cache=shm_cache)

    return stream_list


def gather(shm_and_fps_cache):
    telemetry_data = {}

    # Nuvu stream
    nuvu_raw_stream = toolbox.open_stream_once('nuvu_raw', shm_and_fps_cache)

    if nuvu_raw_stream is not None:  # and session:
        stream_keywords = nuvu_raw_stream.get_keywords()

        telemetry_data['nuvu_temp_ccd'] = stream_keywords['T_CCD']
        telemetry_data['nuvu_temp_controller'] = stream_keywords['T_CNTRLR']
        telemetry_data['nuvu_temp_power_supply'] = stream_keywords['T_PSU']
        telemetry_data['nuvu_temp_fpga'] = stream_keywords['T_FPGA']
        telemetry_data['nuvu_temp_heatsink'] = stream_keywords['T_HSINK']
        telemetry_data['nuvu_emgain'] = stream_keywords['EMGAIN']
        telemetry_data['nuvu_detgain'] = stream_keywords['DETGAIN']
        telemetry_data['nuvu_exposuretime'] = stream_keywords['EXPTIME']
        telemetry_data['nuvu_mframerate'] = stream_keywords['MFRATE']

    # SHWFS process
    shwfs_fps = toolbox.open_fps_once(config.FPS.SHWFS, shm_and_fps_cache)

    if shwfs_fps is not None and shwfs_fps.run_runs():
        telemetry_data['slopes_flux_subaperture_avg'] = shwfs_fps.get_param(
            'flux_subaperture_avg')
        telemetry_data[
            'slopes_flux_subaperture_brightest'] = shwfs_fps.get_param(
                'flux_subaperture_brightest')
        telemetry_data['slopes_residual'] = shwfs_fps.get_param('residual')

    # Tip/tilt stream
    tt_stream = toolbox.open_stream_once(config.Streams.TTM, shm_and_fps_cache)

    if tt_stream is not None:
        # Check turned off to prevent timeout. Data may be obsolete
        tt_data = tt_stream.get_data(check=False)

        telemetry_data['pi_tip'] = float(tt_data[0])
        telemetry_data['pi_tilt'] = float(tt_data[1])

    # DM loop process
    dm_loop_fps = toolbox.open_fps_once('mfilt-1', shm_and_fps_cache)

    if dm_loop_fps is not None and dm_loop_fps.run_runs():
        telemetry_data['dm_loop_gain'] = dm_loop_fps.get_param('loopgain')
        telemetry_data['dm_loop_mult'] = dm_loop_fps.get_param('loopmult')
        telemetry_data['dm_loop_on'] = dm_loop_fps.get_param('loopON')

        if telemetry_data['dm_loop_on'] is True:
            telemetry_data['dm_loop_on'] = 'ON'
        elif telemetry_data['dm_loop_on'] is False:
            telemetry_data['dm_loop_on'] = 'OFF'

    # TTM loop process
    ttm_loop_fps = toolbox.open_fps_once('mfilt-2', shm_and_fps_cache)

    if ttm_loop_fps is not None and ttm_loop_fps.run_runs():
        telemetry_data['ttm_loop_gain'] = ttm_loop_fps.get_param('loopgain')
        telemetry_data['ttm_loop_mult'] = ttm_loop_fps.get_param('loopmult')
        telemetry_data['ttm_loop_on'] = ttm_loop_fps.get_param('loopON')

        if telemetry_data['ttm_loop_on'] is True:
            telemetry_data['ttm_loop_on'] = 'ON'
        elif telemetry_data['ttm_loop_on'] is False:
            telemetry_data['ttm_loop_on'] = 'OFF'

    return telemetry_data
