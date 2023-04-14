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

import numpy as np
import time
import libtmux

from CacaoProcessTools import fps, FPS_status
from pyMilk.interfacing import isio_shmlib

from pyMilk.interfacing.isio_shmlib import SHM

from kalao.cacao import telemetry
from kalao.utils import database
from tcs_communication import t120
from sequencer import system

from configparser import ConfigParser
from pathlib import Path
import os

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
# Read config file
parser = ConfigParser()
parser.read(config_path)

TipMRadPerPixel = parser.getfloat('AO', 'TipMRadPerPixel')
TTSlopeThreshold = parser.getfloat('AO', 'TTSlopeThreshold')
MaxTelOffload = parser.getfloat('AO', 'MaxTelOffload')

CenteringTimeout = parser.getfloat('Starfinder', 'CenteringTimeout')

PixScaleX = parser.getfloat('FLI', 'PixScaleX')
PixScaleY = parser.getfloat('FLI', 'PixScaleY')


def check_stream(stream_name):
    """
    Function verifies if stream_name exists

    :param stream_name: stream to check existence
    :return: boolean, stream_full_path
    """
    # stream_path = Path(os.environ["MILK_SHM_DIR"])
    stream_path = Path('/tmp/milk')
    stream_name = isio_shmlib.check_SHM_name(stream_name) + '.im.shm'
    stream_path = stream_path / stream_name

    if stream_path.exists():
        return True, stream_path
    else:
        return False, stream_path


def check_fps(fps_name):
    """
    Function verifies if fps_name exists

    :param fps_name: fps to check existence
    :return: boolean, stream_full_path
    """
    # fps_path = Path(os.environ["MILK_SHM_DIR"])
    fps_path = Path('/tmp/milk')
    fps_name = isio_shmlib.check_SHM_name(fps_name) + '.fps.shm'
    fps_path = fps_path / fps_name

    if fps_path.exists():
        return True, fps_path
    else:
        return False, fps_path


def close_loop():
    """
    Close the primary DM AO loop followed by the secondary TTM loop.

    :return:
    """

    looprun_exists, looprun_fps_path = check_fps("mfilt-1")

    if not looprun_exists:
        message = f'ERROR: {looprun_fps_path} is missing'
        print(message)
        database.store_obs_log({'ao_log': message})
        system.print_and_log(message)

        return -1

    fps_mfilt1 = fps("mfilt-1")

    # TODO the value to be set is not a float! this line will fail it need to be changed to string
    fps_mfilt1.set_param_value_float('loopON', 'ON')

    ttmloop_exists, ttmloop_fps_path = check_fps("mfilt-2")

    if not ttmloop_exists:
        message = f'ERROR: {ttmloop_fps_path} is missing'
        print(message)
        database.store_obs_log({'ao_log': message})
        system.print_and_log(message)

        return -1

    fps_mfilt2 = fps("mfilt-2")

    # TODO the value to be set is not a float! this line will fail it need to be changed to string
    fps_mfilt2.set_param_value_float('loopON', 'ON')

    return 0


def check_loop():
    # TODO check if loop is running. If loop broken return -1
    pass


def set_dmloop_gain(gain):
    # TODO test

    _set_fps_floatvalue('mfilt-1', 'loopgain', gain)

    return 0


def set_dmloop_mult(mult):
    # TODO test

    _set_fps_floatvalue('mfilt-1', 'loopmult', mult)

    return 0


def set_dmloop_limit(limit):
    # TODO implement

    _set_fps_floatvalue('mfilt-1', 'looplimit', limit)

    return 0


def set_ttmloop_gain(gain):
    # TODO test

    _set_fps_floatvalue('mfilt-2', 'loopgain', gain)

    return 0


def set_ttmloop_mult(mult):
    # TODO test

    _set_fps_floatvalue('mfilt-2', 'loopmult', mult)

    return 0


def set_ttmloop_limit(limit):
    # TODO implement

    _set_fps_floatvalue('mfilt-2', 'looplimit', limit)

    return 0


def set_modal_gain(mode, factor, stream_name='aol1_mgainfact'):
    """
    Function to change the gains of the AO control modes

    :param mode:
    :param factor:
    :param stream_name:
    :return:
    """
    exists, stream_path = check_stream(stream_name)

    mode = int(np.floort(mode))

    if exists:
        mgainfact_shm = SHM(stream_name)
        mgainfact_array = mgainfact_shm.get_data(check=False)

        mgainfact_array[mode] = factor

        mgainfact_shm.set_data(mgainfact_array.astype(mgainfact_shm.nptype))

        return 0

    else:
        return -1


def emgain_off():
    """
    Completely turn of EM gain on the WFS camera. For double safety the command is sent directly to the tmux as well as
    to the nuvu_acquire fps.

    :return: 0 on success
    """

    rValue = -1

    try:
        set_emgain_fps(egain=1)
        rValue = 0
    except Exception as err:
        print('nuvu_acquire fps seems not to be running.')
        print(Exception, err)

    try:
        set_emgain_tmux(egain=1)
        rValue = 0
    except Exception as err:
        print('Unable to connect to nuvu_ctrl tmux. Is the WFS running?')
        print(Exception, err)

    return rValue


def set_emgain_tmux(egain=1):

    server = libtmux.Server()

    try:
        session = server.find_where({"session_name": "nuvu_ctrl"})
    except:
        # TODO specify more precise exception
        session = False

    # If tmux session exists send query temperatures
    if session:
        session.attached_pane.send_keys(f'\ncam.SetEMCalibratedGain({egain})')


def set_emgain_fps(egain=1):

    _set_fps_intvalue('nuvu_acquire-1', 'emgain', str(egain))


def set_exptime_fps(exptime=1):

    _set_fps_intvalue('nuvu_acquire-1', 'exptime', str(exptime))


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

    exists, stream_path = check_stream(stream_name)

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


def tip_tilt_offload(gain=0.2):
    """
    Offload current tip/tilt on the telescope by sending corresponding alt/az offsets.
    The gain can be adjusted to set how much of the tip/tilt should be offloaded.

    :param gain: Gain factor, set to 0.2 by default.
    :return:
    """

    stream_name = "dm02disp"

    tt_exists, tt_fps_path = check_stream(stream_name)

    if not tt_exists:
        return -1

    stream_shm = SHM(stream_name)

    stream_data = stream_shm.get_data(check=False)

    tip = stream_data[0]
    tilt = stream_data[1]

    alt_offload = -tip * (PixScaleX / TipMRadPerPixel) * gain
    az_offload = -tilt * (PixScaleY / TipMRadPerPixel) * gain

    # Keep offsets within defined range
    alt_offload = np.clip(alt_offload, -MaxTelOffload, MaxTelOffload)
    az_offload = np.clip(az_offload, -MaxTelOffload, MaxTelOffload)

    t120.send_offset(az_offload, alt_offload)

    return 0


def tip_tilt_offset(x_tip, y_tilt, absolute=False, stream_name='dm02disp04'):
    """
    Moves the tip tilt mirror by sending an offset in mrad. The value as input is given in pixels and converted.

    :param x_tip: number of pixels to tip
    :param y_tilt: number of pixels to tilt
    :param absolute: Flag to indicate that tip tilt values are in absolute radian. By default, set to False.
    :param stream_name: name of the stream to use to set the offset. dm02disp04 by default.

    :return:
    """

    stream_exists, stream_path = check_stream(stream_name)

    if not stream_exists:
        message = f'ERROR: {stream_path} is missing'
        print(message)
        database.store_obs_log({'ttm_log': message})

        return -1

    stream_shm = SHM(stream_name)

    stream_data = stream_shm.get_data(check=False)

    tip, tilt = stream_data

    # TIP
    if absolute:
        new_tip_value = x_tip
    else:
        new_tip_value = tip + x_tip * TipMRadPerPixel

    if new_tip_value > 2.45:
        print('Limiting tip to 2.45')
        new_tip_value = 2.45
    elif new_tip_value < -2.45:
        print('Limiting tip to -2.45')
        new_tip_value = -2.45

    # TILT
    if absolute:
        new_tilt_value = y_tilt
    else:
        new_tilt_value = tilt + y_tilt * TipMRadPerPixel

    if new_tilt_value > 2.45:
        print('Limiting tilt to 2.45')
        new_tilt_value = 2.45
    elif new_tilt_value < -2.45:
        print('Limiting tilt to -2.45')
        new_tilt_value = -2.45

    stream_data[:] = [new_tilt_value, new_tip_value]

    stream_shm.set_data(stream_data.astype(stream_shm.nptype))

    message = f'Changing Tip and Tilt offset to  {new_tip_value} and {new_tilt_value}'
    print(message)
    database.store_obs_log({'ttm_log': message})

    tip, tilt = stream_data

    message = f'New Tip and Tilt offset values {tip} and {tilt}'
    print(message)
    database.store_obs_log({'ttm_log': message})

    return 0


def tip_tilt_offset_bmc(x_tip, y_tilt, absolute=False):
    """
    Moves the tip tilt mirror by sending an offset in mrad. The value as input is given in pixels and converted.

    :param x_tip: number of pixels to tip
    :param y_tilt: number of pixels to tilt
    :param absolute: Flag to indicate that tip tilt values are in absolute radian. By default, set to False.

    :return:
    """

    bmc_exists, bmc_fps_path = check_fps("bmc_display-01")

    #fps_slopes = fps("shwfs_process")

    if not bmc_exists:
        message = f'ERROR: {bmc_fps_path} is missing'
        print(message)
        database.store_obs_log({'ttm_log': message})
        return -1

    fps_bmc = fps("bmc_display-01")

    # TIP
    #tip = fps_slopes.get_param_value_float('slope_y')
    tip = fps_bmc.get_param_value_float('ttm_tip_offset')

    if absolute:
        new_tip_value = x_tip
    else:
        new_tip_value = tip + x_tip * TipMRadPerPixel

    if new_tip_value > 2.45:
        print('Limiting tip to 2.45')
        new_tip_value = 2.45
    elif new_tip_value < -2.45:
        print('Limiting tip to -2.45')
        new_tip_value = -2.45

    fps_bmc.set_param_value_float('ttm_tip_offset', str(new_tip_value))

    # TILT

    #tilt = fps_slopes.get_param_value_float('slope_x')
    tilt = fps_bmc.get_param_value_float('ttm_tilt_offset')

    if absolute:
        new_tilt_value = y_tilt
    else:
        new_tilt_value = tilt + y_tilt * TipMRadPerPixel

    if new_tilt_value > 2.45:
        print('Limiting tilt to 2.45')
        new_tilt_value = 2.45
    elif new_tilt_value < -2.45:
        print('Limiting tilt to -2.45')
        new_tilt_value = -2.45

    fps_bmc.set_param_value_float('ttm_tilt_offset', str(new_tilt_value))

    message = f'Changing Tip and Tilt offset to  {new_tip_value} and {new_tilt_value}'
    print(message)
    database.store_obs_log({'ttm_log': message})

    tip = fps_bmc.get_param_value_float('ttm_tip_offset')
    tilt = fps_bmc.get_param_value_float('ttm_tilt_offset')

    message = f'New Tip and Tilt offset values {tip} and {tilt}'
    print(message)
    database.store_obs_log({'ttm_log': message})

    return 0


def reset_stream(stream_name):
    """
    Reset the given stream to 0.

    :return:
    """

    stream_exists, stream_path = check_stream(stream_name)

    if stream_exists:
        stream_shm = SHM(stream_name)

        stream_data = stream_shm.get_data(check=False)

        stream_data[:] = 0

        stream_shm.set_data(stream_data.astype(stream_shm.nptype))

    else:
        return -1

    return 0


def wfs_centering(tt_threshold=TTSlopeThreshold):
    """
    Precise tip/tilt centering on the wavefront sensor.

    :param tt_threshold: precision at which the centering need to be based on the residual slope.
    :return:
    """

    tip_centered = False
    tilt_centered = False

    fps_slopes = fps("shwfs_process")
    #fps_bmc = fps("bmc_display-01")
    stream_name = 'dm02disp04'

    stream_exists, stream_path = check_stream(stream_name)

    if not stream_exists:
        message = f'ERROR: {stream_path} is missing'
        print(message)
        database.store_obs_log({'ttm_log': message})

        return -1

    stream_shm = SHM(stream_name)

    #TODO verify that shwfs enough illuminated for centering

    timeout_time = time.time() + CenteringTimeout

    while not (tip_centered and tilt_centered):
        if time.time() > timeout_time:
            system.print_and_log('ERROR centering timeout')

            return -1

        stream_data = stream_shm.get_data(check=False)

        tip_offset, tilt_offset = stream_data

        tip_residual = fps_slopes.get_param_value_float('slope_y')
        tilt_residual = fps_slopes.get_param_value_float('slope_x')

        print(f'Residual tip = {tip_residual}, Residual tilt = {tilt_residual}, tip_offset = {tip_offset}, tilt_offset = {tilt_offset}'
              )

        if np.abs(tip_residual) < tt_threshold:
            tip_centered = True
            new_tip_value = tip_offset
        else:
            # The measured slope tip is about half the value of the negative offset needed to compensate for it
            new_tip_value = tip_offset - tip_residual
            if new_tip_value > 2.45:
                print('Limiting tip to 2.45')
                new_tip_value = 2.45
            elif new_tip_value < -2.45:
                print('Limiting tip to -2.45')
                new_tip_value = -2.45

        if np.abs(tilt_residual) < tt_threshold:
            tilt_centered = True
            new_tilt_value = tilt_offset

        else:
            # The measured slope  in tilt is about half the value of the offset needed to compensate for it
            new_tilt_value = tilt_offset + tilt_residual
            if new_tilt_value > 2.45:
                print('Limiting tip to 2.45')
                new_tilt_value = 2.45
            elif new_tilt_value < -2.45:
                print('Limiting tip to -2.45')
                new_tilt_value = -2.45

        stream_data[:] = [new_tilt_value, new_tip_value]

        stream_shm.set_data(stream_data.astype(stream_shm.nptype))

        time.sleep(1)

    # TODO return 0 if centered, 1 if exceeded iterations
    return 0


def _set_fps_floatvalue(fps_name, key, value):
    # TODO implement
    fps_exists, fps_path = check_fps(fps_name)

    if not fps_exists:
        message = f'ERROR: {fps_path} is missing'
        print(message)
        database.store_obs_log({'ao_log': message})
        system.print_and_log(message)

        return -1

    fps_handle = fps(fps_name)

    fps_handle.set_param_value_float(key, str(value))

    return 0


def _set_fps_intvalue(fps_name, key, value):
    # TODO implement
    fps_exists, fps_path = check_fps(fps_name)

    if not fps_exists:
        message = f'ERROR: {fps_path} is missing'
        print(message)
        database.store_obs_log({'ao_log': message})
        system.print_and_log(message)

        return -1

    fps_handle = fps(fps_name)

    rValue = fps_handle.set_param_value_int(key, str(value))

    return rValue
