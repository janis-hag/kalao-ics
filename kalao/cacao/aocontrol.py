#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : com_tools.py
# @Date : 2022-06-13-09-51
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
aocontrol.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import subprocess
import os
import shutil
import time

import numpy as np
import time

from CacaoProcessTools import fps, FPS_status
from pyMilk.interfacing.isio_shmlib import SHM

from kalao.cacao import telemetry

from configparser import ConfigParser
from pathlib import Path
import os

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
# Read config file
parser = ConfigParser()
parser.read(config_path)

TipMRadPerPixel = parser.getfloat('AO', 'TipMRadPerPixel')


def set_loopgain(gain):
    fps_slopes = fps("shwfs_process")

    return 0


def set_loopmult(mult):

    return 0


def set_looplimit(limit):

    return 0


def set_modal_gain(mode, factor, stream_name='aol1_mgainfact'):
    """
    Function to change the gains of the AO control modes

    :param mode:
    :param factor:
    :param stream_name:
    :return:
    """
    exists, stream_path = telemetry.check_stream(stream_name)

    mode = int(np.floort(mode))

    if exists:
        mgainfact_shm = SHM(stream_name)
        mgainfact_array = mgainfact_shm.get_data(check=False)

        mgainfact_array[mode] = factor

        mgainfact_shm.set_data(mgainfact_array.astype(mgainfact_shm.nptype))

        return 0

    else:
        return -1


def linear_low_pass_modal_gain_filter(cut_off, last_mode=None,
                                      keep_existing_flat=False,
                                      stream_name='aol1_mgainfact'):
    """
    Applies a linear low-pass filter to the ao modal gains. The gain is flat until the cut_off mode where it starts
    decreasing down to zero for the last mode

    :param cut_off: mode at which the gain starts decreasing
    :param last_mode: modes higher than this mode are set to 0
    :param keep_existing_flat: keep the existing gain values instead of setting them to 1
    :param stream_name: name of the milk stream where the gain factor are stored
    :return:
    """

    exists, stream_path = telemetry.check_stream(stream_name)

    if exists:
        mgainfact_shm = SHM(stream_name)
        mgainfact_array = mgainfact_shm.get_data(check=False)

        if not keep_existing_flat:
            mgainfact_array = np.ones(len(mgainfact_array))

        if cut_off > len(mgainfact_array):
            # cut_off frequency has to be within the range of modes. If higher all values will be set to 1
            cut_off = len(mgainfact_array)

        if last_mode is None:
            last_mode = len(mgainfact_array)  #-1
        elif last_mode < cut_off:
            last_mode = cut_off
            mgainfact_array[last_mode:] = 0
        else:
            mgainfact_array[last_mode:] = 0

        if not cut_off == last_mode:
            #down = np.linspace(1, 0, len(mgainfact_array) - cut_off + 2 - (len(mgainfact_array) - last_mode) )[1:-1]
            down = np.linspace(1, 0, last_mode - cut_off + 2)[1:-1]
            mgainfact_array[cut_off:last_mode] = down

        mgainfact_shm.set_data(mgainfact_array.astype(mgainfact_shm.nptype))

        return 0

    else:
        return -1


def tip_tilt_offset(x_tip, y_tilt):
    """
    Moves the tip tilt mirror by sending an offset in mrad. The value as input is given in pixels and converted.

    :param x_tip: number of pixels to tip
    :param y_tilt: number of pixels to tilt
    :return:
    """

    fps_slopes = fps("shwfs_process")
    fps_bmc = fps("bmc_display-01")

    tilt = fps_slopes.get_param_value_float('slope_x')
    tip = fps_slopes.get_param_value_float('slope_y')

    new_tip_value = tip + x_tip * TipMRadPerPixel

    if new_tip_value > 2.45:
        print('Limiting tip to 2.45')
        new_tip_value = 2.45
    elif new_tip_value < -2.45:
        print('Limiting tip to -2.45')
        new_tip_value = -2.45

    fps_bmc.set_param_value_float('ttm_tip_offset', str(new_tip_value))

    new_tilt_value = tilt + y_tilt * TipMRadPerPixel

    if new_tilt_value > 2.45:
        print('Limiting tip to 2.45')
        new_tilt_value = 2.45
    elif new_tilt_value < -2.45:
        print('Limiting tip to -2.45')
        new_tilt_value = -2.45

    fps_bmc.set_param_value_float('ttm_tip_offset', str(new_tip_value))


def wfs_centering(tt_threshold):

    tip_centered = False
    tilt_centered = False

    fps_slopes = fps("shwfs_process")
    fps_bmc = fps("bmc_display-01")

    #TODO add iterations limit to prevent infinite loop
    while not (tip_centered and tilt_centered):

        time.sleep(1)

        tilt = fps_slopes.get_param_value_float('slope_x')
        tip = fps_slopes.get_param_value_float('slope_y')

        tip_offset = fps_bmc.get_param_value_float("ttm_tip_offset")
        tilt_offset = fps_bmc.get_param_value_float("ttm_tilt_offset")

        print(f'tip = {tip}, tilt = {tilt}, tip_offset = {tip_offset}, tilt_offset = {tilt_offset}'
              )

        if np.abs(tip) < tt_threshold:
            tip_centered = True
        else:
            new_tip_value = tip_offset - tip / 2
            if new_tip_value > 2.45:
                print('Limiting tip to 2.45')
                new_tip_value = 2.45
            elif new_tip_value < -2.45:
                print('Limiting tip to -2.45')
                new_tip_value = -2.45

            fps_bmc.set_param_value_float('ttm_tip_offset', str(new_tip_value))

        if np.abs(tilt) < tt_threshold:
            tilt_centered = True
        else:
            new_tilt_value = tilt_offset - tilt / 2
            if new_tilt_value > 2.45:
                print('Limiting tip to 2.45')
                new_tilt_value = 2.45
            elif new_tilt_value < -2.45:
                print('Limiting tip to -2.45')
                new_tilt_value = -2.45

            fps_bmc.set_param_value_float('ttm_tilt_offset',
                                          str(new_tilt_value))

    # TODO return 0 if centered, 1 if exceeded iterations
    return 0
