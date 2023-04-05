#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : telmetry.py
# @Date : 2021-03-18-10-02
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg, Nathanael Restori
"""
The telemetry package contains the tools to store the Adaptive Optics telemetry of KalAO.

"""

from pathlib import Path
from scipy import stats
import numpy as np

import libtmux

from pyMilk.interfacing.isio_shmlib import SHM

from CacaoProcessTools import fps, FPS_status

from kalao.utils import database
from kalao.cacao import fake_data, aocontrol


def create_shm_stream(name):
    """
    Creates a new shared memory SHM stream. If the stream already exists it will reuse it instead of creating a new one.

    :param name: The name to give to the stream.
    :return: Pointer to the stream.
    """

    exists, stream_path = aocontrol.check_stream(name)

    if exists:
        return SHM(str(stream_path))
    else:
        return None


def _get_stream(name, min_value, max_value, sigma_clip=True):
    """
    Opens an existing stream after having verified its existence.

    :param name: Name of the stream to get
    :param min_value: Maximum value to use
    :param max_value: Minimum value to use
    :param sigma_clip: Apply sigma clipping
    :return:
    """

    exists, stream_path = aocontrol.check_stream(name)

    if exists:
        shm_stream = SHM(str(stream_path))
        # Check turned off to prevent timeout. Data may be obsolete
        data = shm_stream.get_data(check=False)

        if sigma_clip:
            data, min_value, max_value = stats.sigmaclip(
                    data, low=2.0, high=2.0)

        if len(data.shape) == 1:
            # One dimensional stream
            return {
                    "data": data.flatten().tolist(),
                    "width": 1,
                    "height": data.shape[0],
                    "min": min_value,
                    "max": max_value
            }
        else:
            return {
                    "data": data.flatten().tolist(),
                    "width": data.shape[1],
                    "height": data.shape[0],
                    "min": min_value,
                    "max": max_value
            }

    else:
        return {"data": 0, "width": 0, "height": 0, "min": 0, "max": 0}


def get_stream_data(shm_stream, name, min_value, max_value):
    """
    Reads and already open shm_stream, after having verified that the stream with that name exists.

    :param shm_stream: The stream to read
    :param name: stream name
    :param min_value: minimal value in the stream
    :param max_value: maximal value in the stream
    :return: Dictionary with: data, width, height, min, max
    """

    exists, stream_path = aocontrol.check_stream(name)

    if exists:
        try:
            data = shm_stream.get_data(check=False)
            list = data.flatten().tolist()

            if len(data.shape) == 1:
                # One dimensional stream
                width = 1
                height = data.shape[0]
            else:
                width = data.shape[1]
                height = data.shape[0]
            return {
                    "data": list,
                    "width": width,
                    "height": height,
                    "min": min(list),
                    "max": max(list)
            }
        except:
            return {"data": 0, "width": 0, "height": 0, "min": 0, "max": 0}
    else:
        return {"data": 0, "width": 0, "height": 0, "min": 0, "max": 0}


def streams(realData=True):
    """
    Provides all the streams needed for the KalAO GUI.

    :param realData: Flag to turn on random data for GUI testing purposes
    :return: dictionary with all the stream contents
    """

    if not realData:
        # Returning fake streams for testing purposes
        return fake_data.fake_streams()
    else:
        stream_list = {}

        stream_list["nuvu_stream"] = _get_stream(name="nuvu_stream",
                                                 min_value=0,
                                                 max_value=2**16 - 1)
        stream_list["shwfs_slopes"] = _get_stream(name="shwfs_slopes",
                                                  min_value=-2, max_value=2)
        stream_list["dm01disp"] = _get_stream(name="dm01disp", min_value=-1.75,
                                              max_value=1.75)
        stream_list["shwfs_slopes_flux"] = _get_stream(
                name="shwfs_slopes_flux", min_value=0,
                max_value=4 * (2**16 - 1))
        stream_list["aol1_mgainfact"] = _get_stream(name="aol1_mgainfact",
                                                    min_value=0, max_value=1)
        # streams["aol1_modeval"] = _get_stream("aol1_modeval", -1.75, 1.75) # TODO: uncomment when modal control is working

        return stream_list


def telemetry_save(stream_list):
    """
    Saves all the adaptive optics telemetry on the mongo database.

    :param stream_list: A list containing pointers to all the already opened streams.
    :return: status code
    """

    telemetry_data = {}

    # NUVU process
    # check if SHM exists and is running
    nuvu_exists, nuvu_stream_path = aocontrol.check_stream("nuvu_raw")

    server = libtmux.Server()
    try:
        session = server.find_where({"session_name": "nuvu_ctrl"})
    except:
        # TODO specify more precise exception
        session = False

    # If tmux session exists send query temperatures
    if session:
        session.attached_pane.send_keys('\ncam.GetTemperature()')

    if nuvu_exists and session:
        if stream_list['nuvu_stream'] is None:
            stream_list['nuvu_stream'] = SHM("nuvu_raw")

        stream_keywords = stream_list['nuvu_stream'].get_keywords()

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

    # Create the in-memory "file"
    # temp_out = io.StringIO()

    # NUVU process
    #check if fps exists and is running
    # nuvu_exists, nuvu_fps_path = aocontrol.check_fps("nuvu_acquire")
    #
    # if nuvu_exists:
    #     sys.stdout = temp_out
    #     fps_nuvu = fps("nuvu_acquire")
    #     sys.stdout = sys.__stdout__
    #
    #     # Check if it's running
    # 	if fps_nuvu.RUNrunning==1:
    #         telemetry_data["nuvu_temp_ccd"]          = fps_nuvu["nuvu_acquire.temp_ccd"]
    #         telemetry_data["nuvu_temp_controller"]   = fps_nuvu["nuvu_acquire.temp_controller"]
    #         telemetry_data["nuvu_temp_power_supply"] = fps_nuvu["nuvu_acquire.temp_power_supply"]
    #         telemetry_data["nuvu_temp_fpga"]         = fps_nuvu["nuvu_acquire.temp_fpga"]
    #         telemetry_data["nuvu_temp_heatsink"]     = fps_nuvu["nuvu_acquire.temp_heatsink"]
    #         telemetry_data["nuvu_emgain"]            = fps_nuvu["nuvu_acquire.emgain"]
    #         telemetry_data["nuvu_exposuretime"]      = fps_nuvu["nuvu_acquire.exposuretime"]
    #
    # else:
    #     pass # Return empty streams
    #

    # SHWFS process
    # check if fps exists and is running
    shwfs_exists, shwfs_fps_path = aocontrol.check_fps("shwfs_process")

    # APO-Q-P240-R8,6 FOV per subap / pixels_per_subap
    pixel_scale = 5.7929690265142 / 5

    if shwfs_exists:
        if stream_list['fps_slopes'] is None:
            stream_list['fps_slopes'] = fps("shwfs_process")

        # Check if it's running
        if stream_list['fps_slopes'].RUNrunning == 1:
            telemetry_data["slopes_flux_subaperture"] = stream_list[
                    'fps_slopes'].get_param_value_float('flux_subaperture')
            telemetry_data["slopes_residual_pix"] = stream_list[
                    'fps_slopes'].get_param_value_float('residual')
            telemetry_data["slopes_residual_arcsec"] = stream_list[
                    'fps_slopes'].get_param_value_float(
                            'residual') * pixel_scale

    # Tip/tilt stream
    # check if fps exists and is running
    tt_exists, tt_fps_path = aocontrol.check_stream("dm02disp")

    if tt_exists:
        if stream_list['tt_stream'] is None:
            stream_list['tt_stream'] = SHM("dm02disp")
            # stream_list['tt_stream'].close()
        # else:
        # stream_list['tt_stream'] = SHM("dm02disp")

        # Check turned off to prevent timeout. Data may be obsolete
        tt_data = stream_list['tt_stream'].get_data(check=False)

        telemetry_data["pi_tip"] = float(tt_data[0])
        telemetry_data["pi_tilt"] = float(tt_data[1])

    # looopRUN process
    # check if fps exists and is running
    looprun_exists, looprun_fps_path = aocontrol.check_fps("mfilt-1")

    if looprun_exists:
        if stream_list['mfilt-1'] is None:
            stream_list['mfilt-1'] = fps("mfilt-1")

        # Check if it's running
        if stream_list['mfilt-1'].RUNrunning == 1:
            telemetry_data["loop_gain"] = stream_list[
                    'mfilt-1'].get_param_value_float('loopgain')
            telemetry_data["loop_mult"] = stream_list[
                    'mfilt-1'].get_param_value_float('loopmult')
            # loopOn 0 = OFF, 1 = ON
            telemetry_data["loop_on"] = stream_list[
                    'mfilt-1'].get_param_value_int('loopON')
            if telemetry_data["loop_on"] == 1:
                telemetry_data["loop_on"] = 'ON'
            elif telemetry_data["loop_on"] == 0:
                telemetry_data["loop_on"] = 'OFF'

    # check if fps exists and is running
    tt_loop_exists, looprun_fps_path = aocontrol.check_fps("mfilt-2")

    if tt_loop_exists:
        if stream_list['mfilt-2'] is None:
            stream_list['mfilt-2'] = fps("mfilt-2")

        # Check if it's running
        if stream_list['mfilt-2'].RUNrunning == 1:
            telemetry_data["tt_loop_gain"] = stream_list[
                    'mfilt-2'].get_param_value_float('loopgain')
            telemetry_data["tt_loop_mult"] = stream_list[
                    'mfilt-2'].get_param_value_float('loopmult')
            # loopOn 0 = OFF, 1 = ON
            telemetry_data["tt_loop_on"] = stream_list[
                    'mfilt-2'].get_param_value_int('loopON')
            if telemetry_data["tt_loop_on"] == 1:
                telemetry_data["tt_loop_on"] = 'ON'
            elif telemetry_data["tt_loop_on"] == 0:
                telemetry_data["tt_loop_on"] = 'OFF'

    database.store_telemetry(telemetry_data)

    # return nuvu_stream, tt_stream, fps_slopes

    return 0


def wfs_illumination_fraction(wfs_threshold):
    """
    Function reads the nuvu stream and return the summed flux in each subaperture

    :return: subapertures summed flux
    """

    # TODO implement masking procedure in order to only consider useful subaps

    shwfs_stream = _get_stream("shwfs_slopes_flux", 0, 4 * (2**16 - 1))

    shwfs_array = np.array(shwfs_stream['data'])

    illuminated_pupil_fraction = (shwfs_array >
                                  wfs_threshold).sum() / len(shwfs_array)

    # TODO reject subaps out of centering zone

    return illuminated_pupil_fraction
