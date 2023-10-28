#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : telmetry.py
# @Date : 2021-03-18-10-02
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg, Nathanael Restori
"""
The telemetry package contains the tools to store the Adaptive Optics telemetry of KalAO.

"""


import numpy as np

import libtmux

from pyMilk.interfacing.isio_shmlib import SHM

from kalao.utils import database
from kalao.cacao import fake_data, aocontrol, toolbox

import traceback

import kalao_config as config


def _get_stream(name, min_value_th, max_value_th, shm_stream=None):
    """
    Get stream data, after having verified that the stream with that name exists.

    :param shm_stream: The stream to read
    :param name: stream name
    :param min_value_th: theoretical minimal value in the stream
    :param max_value_th: theoretical maximal value in the stream
    :param shm_stream: Stream already opened
    :return: Dictionary with: data, width, height, min, max, min_th, max_th
    """

    exists, stream_path = aocontrol.check_stream(name)

    if exists:
        try:
            if shm_stream is None:
                shm_stream = SHM(stream_path)

            data = shm_stream.get_data(check=False)

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
            return {
                    "data": 0,
                    "width": 0,
                    "height": 0,
                    "min": 0,
                    "max": 0,
                    "min_th": 0,
                    "max_th": 0
            }
    else:
        return {
                "data": 0,
                "width": 0,
                "height": 0,
                "min": 0,
                "max": 0,
                "min_th": 0,
                "max_th": 0
        }


def streams(realData=True, shm_streams={}):
    """
    Provides all the streams needed for the KalAO GUI.

    :param realData: Flag to turn on random data for GUI testing purposes
    :param shm_streams: Dictionary of open streams
    :return: dictionary with all the stream contents
    """

    if not realData:
        # Returning fake streams for testing purposes
        return fake_data.fake_streams()
    else:
        stream_list = {}

        stream_list["nuvu_stream"] = _get_stream(
                name="nuvu_stream", min_value_th=0, max_value_th=2**16 - 1,
                shm_stream=shm_streams.get("nuvu_stream"))

        stream_list["shwfs_slopes"] = _get_stream(
                name="shwfs_slopes", min_value_th=-2, max_value_th=2,
                shm_stream=shm_streams.get("shwfs_slopes"))

        stream_list["dm01disp"] = _get_stream(
                name="dm01disp", min_value_th=-1.75, max_value_th=1.75,
                shm_stream=shm_streams.get("dm01disp"))

        stream_list["shwfs_slopes_flux"] = _get_stream(
                name="shwfs_slopes_flux", min_value_th=0, max_value_th=4 *
                (2**16 - 1), shm_stream=shm_streams.get("shwfs_slopes_flux"))

        stream_list["aol1_mgainfact"] = _get_stream(
                name="aol1_mgainfact", min_value_th=0, max_value_th=1,
                shm_stream=shm_streams.get("aol1_mgainfact"))

        # streams["aol1_modeval"] = _get_stream("aol1_modeval", -1.75, 1.75) # TODO: uncomment when modal control is working

        return stream_list


def telemetry_save(stream_and_fps_list):
    """
    Saves all the adaptive optics telemetry on the mongo database.

    :param stream_list: A list containing pointers to all the already opened streams.
    :return: status code
    """

    telemetry_data = {}

    # NUVU process
    server = libtmux.Server()
    try:
        session = server.find_where({"session_name": "nuvu_ctrl"})
    except:
        # TODO specify more precise exception
        session = False

    # If tmux session exists send query temperatures
    if session:
        session.attached_pane.send_keys('\ncam.GetTemperature()')

    nuvu_stream = toolbox.open_stream_once('nuvu_raw', stream_and_fps_list)

    if nuvu_stream is not None and session:
        stream_keywords = nuvu_stream.get_keywords()

        # Check if it's running
        # if fps_nuvu.RUNrunning==1:
        telemetry_data["nuvu_temp_ccd"] = stream_keywords['T_CCD']
        telemetry_data["nuvu_temp_controller"] = stream_keywords['T_CNTRLR']
        telemetry_data["nuvu_temp_power_supply"] = stream_keywords['T_PSU']
        telemetry_data["nuvu_temp_fpga"] = stream_keywords['T_FPGA']
        telemetry_data["nuvu_temp_heatsink"] = stream_keywords['T_HSINK']
        telemetry_data["nuvu_emgain"] = stream_keywords['EMGAIN']
        telemetry_data["nuvu_detgain"] = stream_keywords['DETGAIN']
        telemetry_data["nuvu_exposuretime"] = stream_keywords['EXPTIME']
        telemetry_data["nuvu_mframerate"] = stream_keywords['MFRATE']

    else:
        # Return empty streams
        pass

    # SHWFS process
    slopes_stream = toolbox.open_fps_once('shwfs_process-1',
                                          stream_and_fps_list)

    if slopes_stream is not None:
        # Check if it's running
        if slopes_stream.RUNrunning == 1:
            telemetry_data[
                    "slopes_flux_subaperture"] = slopes_stream.get_param_value_float(
                            'flux_subaperture')
            telemetry_data[
                    "slopes_residual_pix"] = slopes_stream.get_param_value_float(
                            'residual')
            telemetry_data[
                    "slopes_residual_arcsec"] = slopes_stream.get_param_value_float(
                            'residual') * config.WFS.plate_scale

    # Tip/tilt stream
    # check if fps exists and is running
    tt_stream = toolbox.open_stream_once('dm02disp', stream_and_fps_list)

    if tt_stream is not None:
        # Check turned off to prevent timeout. Data may be obsolete
        tt_data = tt_stream.get_data(check=False)

        telemetry_data["pi_tip"] = float(tt_data[0])
        telemetry_data["pi_tilt"] = float(tt_data[1])

    # looopRUN process
    # check if fps exists and is running
    dm_loop_stream = toolbox.open_fps_once('mfilt-1', stream_and_fps_list)

    if dm_loop_stream is not None:
        # Check if it's running
        if dm_loop_stream.RUNrunning == 1:
            telemetry_data["loop_gain"] = dm_loop_stream.get_param_value_float(
                    'loopgain')
            telemetry_data["loop_mult"] = dm_loop_stream.get_param_value_float(
                    'loopmult')
            telemetry_data["loop_on"] = dm_loop_stream.get_param_value_int(
                    'loopON')

            if telemetry_data["loop_on"] == 1:
                telemetry_data["loop_on"] = 'ON'
            elif telemetry_data["loop_on"] == 0:
                telemetry_data["loop_on"] = 'OFF'

    # check if fps exists and is running
    ttm_loop_stream = toolbox.open_fps_once('mfilt-2', stream_and_fps_list)

    if ttm_loop_stream is not None:
        # Check if it's running
        if ttm_loop_stream.RUNrunning == 1:
            telemetry_data[
                    "tt_loop_gain"] = ttm_loop_stream.get_param_value_float(
                            'loopgain')
            telemetry_data[
                    "tt_loop_mult"] = ttm_loop_stream.get_param_value_float(
                            'loopmult')
            telemetry_data["tt_loop_on"] = ttm_loop_stream.get_param_value_int(
                    'loopON')

            if telemetry_data["tt_loop_on"] == 1:
                telemetry_data["tt_loop_on"] = 'ON'
            elif telemetry_data["tt_loop_on"] == 0:
                telemetry_data["tt_loop_on"] = 'OFF'

    database.store_telemetry(telemetry_data)

    return 0
