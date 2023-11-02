#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : com_tools.py
# @Date : 2022-06-13-09-51
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
aocontrol.py is part of the KalAO Instrument Control Software (KalAO-ICS).
"""

import time

import numpy as np
import pandas as pd

from pyMilk.interfacing.shm import SHM

import libtmux

from kalao import ippower
from kalao.cacao import toolbox
from kalao.utils import database
from sequencer import system
from tcs_communication import t120

import kalao_config as config
from kalao_enums import IPPowerStatus, LoopStatus

shm_and_fps_cache = {}


def close_loop():
    """
    Close the primary DM AO loop followed by the secondary TTM loop.

    :return:
    """

    fps_mfilt1 = toolbox.open_fps_once("mfilt-1", shm_and_fps_cache)

    if fps_mfilt1 is None:
        message = f'ERROR: mfilt-1 is missing'
        print(message)
        database.store_obs_log({'ao_log': message, 'obs_log': message})

        return -1

    fps_mfilt1.set_param('loopON', True)

    fps_mfilt2 = toolbox.open_fps_once("mfilt-2", shm_and_fps_cache)

    if fps_mfilt2 is None:
        message = f'ERROR: mfilt-2 is missing'
        print(message)
        database.store_obs_log({'ao_log': message, 'obs_log': message})

        return -1

    fps_mfilt2.set_param('loopON', True)

    return 0


def check_loop():
    status = LoopStatus(0)

    fps_mfilt1 = toolbox.open_fps_once("mfilt-1", shm_and_fps_cache)

    if fps_mfilt1 is not None and fps_mfilt1.get_param('loopON'):
        status |= LoopStatus.DM_LOOP_ON

    fps_mfilt2 = toolbox.open_fps_once("mfilt-2", shm_and_fps_cache)

    if fps_mfilt2 is not None and fps_mfilt2.get_param('loopON'):
        status |= LoopStatus.TTM_LOOP_ON

    return status


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
    mgainfact_stream = toolbox.open_stream_once(stream_name,
                                                shm_and_fps_cache)

    mode = int(np.floort(mode))

    if mgainfact_stream is not None:
        mgainfact_array = mgainfact_stream.get_data(check=False)

        mgainfact_array[mode] = factor

        mgainfact_stream.set_data(mgainfact_array, True)

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
        _set_emgain_fps(emgain=1)
        rValue = 0
    except Exception as err:
        print('nuvu_acquire fps seems not to be running.')
        print(Exception, err)

    try:
        _set_emgain_tmux(emgain=1)
        rValue = 0
    except Exception as err:
        print('Unable to connect to nuvu_ctrl tmux. Is the WFS running?')
        print(Exception, err)

    return rValue


def set_emgain(emgain=1, method='tmux'):
    """
    Set the EM gain of the Nuvu WFS camera.

    :param emgain: EM gain to set. 1 by default for no gain.
    :return:
    """

    emgain = int(emgain)

    if emgain > config.AO.WFS_max_emgain:
        emgain = config.AO.WFS_max_emgain

    elif emgain < 1:
        emgain = 1

    if method == 'fps':
        _set_emgain_fps(emgain)
    elif method == 'tmux':
        _set_emgain_tmux(emgain)
    else:
        message = f'ERROR: unknown {method=} in set_emgain'
        print(message)
        database.store_obs_log({'ao_log': message, 'obs_log': message})


def set_exptime(exptime=0, method='tmux'):
    """
    Set the exposure time of the Nuvu WFS camera.

    :param exptime: exposure time to set in milliseconds. 0 by default for highest frame rate.
    :return:
    """

    if exptime < 0:
        exptime = 0

    if method == 'fps':
        _set_exptime_fps(exptime)
    elif method == 'tmux':
        _set_exptime_tmux(exptime)
    else:
        message = f'ERROR: unknown {method=} in set_exptime'
        print(message)
        database.store_obs_log({'ao_log': message, 'obs_log': message})


def linear_low_pass_modal_gain_filter(cut_off=None, last_mode=None,
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

    if cut_off is None and last_mode is None:
        return -1
    elif cut_off is None:
        cut_off = last_mode
    elif last_mode is None:
        last_mode = cut_off

    mgainfact_stream = toolbox.open_stream_once(stream_name,
                                                shm_and_fps_cache)

    if mgainfact_stream is not None:
        mgainfact_array = mgainfact_stream.get_data(check=False)

        if not keep_existing_flat:
            mgainfact_array = np.ones(len(mgainfact_array))

        if cut_off > len(mgainfact_array):
            # cut_off frequency has to be within the range of modes. If higher all values will be set to 1
            cut_off = len(mgainfact_array)

        if last_mode is None:
            last_mode = len(mgainfact_array)  # -1
        elif last_mode < cut_off:
            last_mode = cut_off
            mgainfact_array[last_mode:] = 0
        else:
            mgainfact_array[last_mode:] = 0

        if not cut_off == last_mode:
            # down = np.linspace(1, 0, len(mgainfact_array) - cut_off + 2 - (len(mgainfact_array) - last_mode) )[1:-1]
            down = np.linspace(1, 0, last_mode - cut_off + 2)[1:-1]
            mgainfact_array[cut_off:last_mode] = down

        mgainfact_stream.set_data(mgainfact_array, True)

        return 0

    else:
        return -1


def tip_tilt_offload_ttm_to_telescope(gain=0.25, override_threshold=False,
                                      stream_name="dm02disp"):
    """
    Offload current tip/tilt on the telescope by sending corresponding alt/az offsets.
    The gain can be adjusted to set how much of the tip/tilt should be offloaded.

    :param gain: Gain factor, set to 0.25 by default.
    :return:
    """

    ttm_stream = toolbox.open_stream_once(stream_name, shm_and_fps_cache)

    if ttm_stream is None:
        return -1

    stream_data = ttm_stream.get_data(check=False)

    tip = stream_data[0]
    tilt = stream_data[1]

    offload = np.sqrt(tip**2 + tilt**2)

    if override_threshold or offload > config.TTM.offload_threshold:
        alt_offload = tip * config.TTM.tip_to_onsky * gain
        az_offload = tilt * config.TTM.tilt_to_onsky * gain

        # Keep offsets within defined range
        alt_offload = np.clip(alt_offload, -config.TTM.max_tel_offload,
                              config.TTM.max_tel_offload)
        az_offload = np.clip(az_offload, -config.TTM.max_tel_offload,
                             config.TTM.max_tel_offload)

        t120.send_offset(alt_offload, az_offload)

    return 0


def tip_tilt_offset_fli_to_ttm(x_tip, y_tilt, absolute=False,
                               stream_name='dm02disp04'):
    """
    Moves the tip tilt mirror by sending an offset in mrad. The value as input is given in pixels and converted.

    :param x_tip: number of pixels to tip
    :param y_tilt: number of pixels to tilt
    :param absolute: Flag to indicate that tip tilt values are in absolute radian. By default, set to False.
    :param stream_name: name of the stream to use to set the offset. dm02disp04 by default.

    :return:
    """

    ttm_stream = toolbox.open_stream_once(stream_name, shm_and_fps_cache)

    if ttm_stream is None:
        message = f'ERROR: {stream_name} is missing'
        print(message)
        database.store_obs_log({'ttm_log': message})

        return -1

    stream_data = ttm_stream.get_data(check=False)

    tip, tilt = stream_data

    # TIP
    if absolute:
        new_tip_value = x_tip
    else:
        new_tip_value = tip + x_tip * config.AO.FLI_tip_to_TTM

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
        new_tilt_value = tilt + y_tilt * config.AO.FLI_tilt_to_TTM

    if new_tilt_value > 2.45:
        print('Limiting tilt to 2.45')
        new_tilt_value = 2.45
    elif new_tilt_value < -2.45:
        print('Limiting tilt to -2.45')
        new_tilt_value = -2.45

    stream_data[:] = [new_tip_value, new_tilt_value]

    ttm_stream.set_data(stream_data, True)

    message = f'Changing Tip and Tilt offset to  {new_tip_value} and {new_tilt_value}'
    print(message)
    database.store_obs_log({'ttm_log': message})

    tip, tilt = stream_data

    message = f'New Tip and Tilt offset values {tip} and {tilt}'
    print(message)
    database.store_obs_log({'ttm_log': message})

    return 0


def turn_dm_on(fps_list={}):
    system.print_and_log("Turning on DM")

    time.sleep(1)

    bmc_display_fps = toolbox.open_fps_once('bmc_display-01', fps_list)

    rValue = ippower.switch_ippower(config.IPPower.Port.BMC_DM,
                                    IPPowerStatus.ON)

    if rValue != IPPowerStatus.ON:
        return -1

    time.sleep(config.Watchdog.dm_wait_betweeen_actions)

    if bmc_display_fps is not None:
        bmc_display_fps.run_start()

    time.sleep(config.Watchdog.dm_wait_betweeen_actions)

    reset_dm(config.AO.DM_loop_number)

    # TODO check that the fps managed to start and adapt return value accordingly

    if rValue == IPPowerStatus.ON:
        return 0
    else:
        return -1


def turn_dm_off(fps_list={}):
    system.print_and_log("Turning off DM")

    time.sleep(1)

    bmc_display_fps = toolbox.open_fps_once('bmc_display-01', fps_list)

    reset_dm(config.AO.DM_loop_number)

    time.sleep(config.Watchdog.dm_wait_betweeen_actions)

    if bmc_display_fps is not None:
        bmc_display_fps.run_stop()

    time.sleep(config.Watchdog.dm_wait_betweeen_actions)

    rValue = ippower.switch_ippower(config.IPPower.Port.BMC_DM,
                                    IPPowerStatus.OFF)

    if rValue == IPPowerStatus.OFF:
        return 0
    else:
        return -1

    return 0


def reset_dm(dm_number):
    ret = 0

    for i in range(0, 12):
        stream_name = f'dm{dm_number:02d}disp{i:02d}'
        ret += toolbox.zero_stream(stream_name)

    return ret


def reset_all_dms(max_dm_number=2):
    ret = 0

    for i in range(1, max_dm_number + 1):
        ret += reset_dm(i)

    return ret


def wfs_centering(tt_threshold=config.AO.WFS_centering_slope_threshold):
    """
    Precise tip/tilt centering on the wavefront sensor.

    :param tt_threshold: precision at which the centering need to be based on the residual slope.
    :return:
    """

    tip_centered = False
    tilt_centered = False

    dm_stream = toolbox.open_stream_once('dm02disp04', shm_and_fps_cache)
    slopes_fps = toolbox.open_fps_once('shwfs_process-1', shm_and_fps_cache)

    if dm_stream is None:
        message = f'ERROR: dm02disp04 is missing'
        print(message)
        database.store_obs_log({'ttm_log': message})

        return -1

    if slopes_fps is None:
        message = f'ERROR: shwfs_process is missing'
        print(message)
        database.store_obs_log({'ttm_log': message})

        return -1

    # TODO verify that shwfs enough illuminated for centering

    timeout_time = time.time() + config.Starfinder.centering_timeout

    while not (tip_centered and tilt_centered):
        if time.time() > timeout_time:
            system.print_and_log('ERROR WFS centering timeout')

            return -1

        stream_data = dm_stream.get_data(check=False)

        tip_offset, tilt_offset = stream_data

        tip_residual = slopes_fps.get_param(
                'slope_y') * config.AO.WFS_tip_to_TTM
        tilt_residual = slopes_fps.get_param(
                'slope_x') * config.AO.WFS_tilt_to_TTM

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
            new_tilt_value = tilt_offset - tilt_residual
            if new_tilt_value > 2.45:
                print('Limiting tip to 2.45')
                new_tilt_value = 2.45
            elif new_tilt_value < -2.45:
                print('Limiting tip to -2.45')
                new_tilt_value = -2.45

        stream_data[:] = [new_tip_value, new_tilt_value]
        print(f'Residual tip = {tip_residual}, Residual tilt = {tilt_residual}, previous tip_offset = {tip_offset}, previous tilt_offset = {tilt_offset}, {new_tip_value=}, {new_tilt_value=}'
              )
        dm_stream.set_data(stream_data.astype(dm_stream.nptype))

        time.sleep(1)

    # TODO return 0 if centered, 1 if exceeded iterations
    return 0


def dm_poke_sequence(timestep=0.1, stream_name="dm01disp09"):
    stream_exists, stream_name = toolbox.check_stream(stream_name)

    dmdisp = SHM(stream_name)

    # initial_shape = dmdisp.get_data(check=False)
    dm_array = np.zeros(dmdisp.shape, dmdisp.nptype)
    dmdisp.set_data(dm_array, True)

    # Two round one with pokes up and one with pokes down
    for i in range(2):
        # poke = 1 / 2 + 0.25 - 0.5 * i - 0.5
        poke = i - 1  # -1, 0

        for iy, ix in np.ndindex(dmdisp.shape):
            print(iy, ix)
            dm_array = np.ones(dmdisp.shape, dmdisp.nptype) - i  # 0, 1
            dm_array[iy, ix] = poke
            dmdisp.set_data(dm_array, True)
            time.sleep(timestep)

    # Clear DM before exiting
    dm_array = np.zeros(dmdisp.shape, dmdisp.nptype)
    dmdisp.set_data(dm_array, True)

    # Clear DM before exiting
    dm_array = np.zeros(dmdisp.shape, dmdisp.nptype)
    dmdisp.set_data(dm_array, True)


def actuator_response_sequence(timestep=0.1):
    dmdisp = SHM("dm01disp09")
    shwfs_slopes = SHM('shwfs_slopes')

    initial_shape = dmdisp.get_data(check=False)
    # dm_array = np.zeros(dmdisp.shape, dmdisp.nptype)

    # # Two round one with pokes up and one with pokes down
    # for i in range(2):
    #     #poke = 1 / 2 + 0.25 - 0.5 * i - 0.5
    #     poke = i -1   # -1, 0

    response_sequence = None

    for ix, iy in np.ndindex(dmdisp.shape):
        print(ix, iy)
        if ix in [0, 11] or iy in [
                0, 11
        ]:  # skip actuators at the edge, i.e. ix or iy equal to 0 or 11
            continue

        single_response = single_actuator_response(ix, iy, dmdisp,
                                                   shwfs_slopes, timestep)
        #
        # print(iy, ix)
        # dm_array = np.ones(dmdisp.shape, dmdisp.nptype) - i # 0, 1
        # dm_array[iy, ix] = poke
        # dmdisp.set_data(dm_array, True)
        # time.sleep(timestep)
        if response_sequence is None:
            response_sequence = single_response
        else:
            response_sequence = pd.concat([response_sequence, single_response],
                                          axis=1)

    # Clear DM before exiting
    dm_array = np.zeros(dmdisp.shape, dmdisp.nptype)
    dmdisp.set_data(dm_array, True)

    # Clear DM before exiting
    dmdisp.set_data(initial_shape, True)

    return response_sequence


def single_actuator_response(ix, iy, dmdisp, shwfs_slopes, timestep=1):
    #    Actuator 2,3 = > subaps: 1,2 1,3 2,2 2,3
    #    ix, iy => ix,iy ix,iy-1 ix-1,iy-1, ix-1, iy

    br = (ix, iy)
    bl = (ix, iy - 1)
    tl = (ix - 1, iy - 1)
    tr = (ix - 1, iy)

    br2 = (ix, iy + 11)
    bl2 = (ix, iy - 1 + 11)
    tl2 = (ix - 1, iy - 1 + 11)
    tr2 = (ix - 1, iy + 11)

    dm_array = -0.5 * np.ones(dmdisp.shape, dmdisp.nptype)

    slopes_xy_list = []

    slopes_stack = None

    for poke_amplitude in np.arange(-0.5, 0.51, 1 / 20):

        dm_array[ix, iy] = poke_amplitude
        dmdisp.set_data(dm_array, True)
        dmdisp.set_data(dm_array, True)

        slopes_data = shwfs_slopes.get_data(check=False)
        if slopes_stack is None:
            slopes_stack = slopes_data
        else:
            slopes_stack = np.dstack((slopes_stack, slopes_data))

        slopes_xy_list.append({
                'poke_amplitude': np.round(poke_amplitude, 3),
                'tl': slopes_data[tl],
                'tl2': slopes_data[tl2],
                'bl': slopes_data[bl],
                'bl2': slopes_data[bl2],
                'tr': slopes_data[tr],
                'tr2': slopes_data[tr2],
                'br': slopes_data[br],
                'br2': slopes_data[br2],
        })

        time.sleep(timestep)

    slopes_xy = pd.DataFrame.from_records(slopes_xy_list)

    # Removing zero-offset in order to keep only positive values
    for column in slopes_xy.columns[1:]:  # excluding col. 0: poke_amplitude
        slopes_xy[column] = slopes_xy[column] - slopes_xy[column].min()

        if slopes_xy[column][1:10].mean() > slopes_xy[column][10:].mean(
        ):  # invert order if values are decreasing
            slopes_xy[column] = slopes_xy[column].values[::-1]

    slopes_xy = pd.concat([
            slopes_xy.poke_amplitude, slopes_xy[list(slopes_xy)[1:]].sum(
                    axis=1).rename(str(ix) + '_' + str(iy))
    ], axis=1).set_index('poke_amplitude')

    dm_array = np.zeros(dmdisp.shape, dmdisp.nptype)
    dmdisp.set_data(dm_array, True)

    return slopes_xy


def dm_flat_poke(timestep=0.1):
    dmdisp = SHM("dm01disp09")
    dmdip0 = SHM("dm01disp")

    shwfs_slopes = SHM('shwfs_slopes')

    initial_shape = dmdisp.get_data(check=False)

    slopes_xy_list = []

    slopes_stack = None

    amplitude_range = np.arange(-2, 2, 1 / 100)

    for poke_amplitude in amplitude_range:

        dm_array = np.ones(dmdisp.shape, dmdisp.nptype) * poke_amplitude
        dmdisp.set_data(dm_array, True)
        print(poke_amplitude, np.mean(dmdip0.get_data(check=False)))
        time.sleep(timestep)
        slopes_data = shwfs_slopes.get_data(check=False)
        if slopes_stack is None:
            slopes_stack = slopes_data
        else:
            slopes_stack = np.dstack((slopes_stack, slopes_data))

    # Clear DM before exiting
    dm_array = np.zeros(dmdisp.shape, dmdisp.nptype)
    dmdisp.set_data(dm_array, True)
    dm_array = np.ones(dmdisp.shape, dmdisp.nptype) * (-2)
    dmdisp.set_data(dm_array, True)

    dmdisp.set_data(initial_shape, True)

    # Remove initial slope offset
    slopes_stack = np.rollaxis(slopes_stack, 2) - slopes_stack[:, :, 0]

    # Put amplitude on first axis
    #slopes_stack = np.rollaxis(slopes_stack, 2)

    actuator_response = np.zeros([
            slopes_stack.shape[0], dmdisp.shape[0], dmdisp.shape[1]
    ])
    actuator_response_df = None

    # Get actuator response
    for ix, iy in np.ndindex(dmdisp.shape):
        if ix in [0, 11] or iy in [
                0, 11
        ]:  # skip actuators at the edge, i.e. ix or iy equal to 0 or 11
            continue

        actuator_response[:, ix, iy] = np.sum(
                np.abs([
                        slopes_stack[:, ix, iy], slopes_stack[:, ix, iy - 1],
                        slopes_stack[:, ix - 1,
                                     iy - 1], slopes_stack[:, ix - 1, iy],
                        slopes_stack[:, ix,
                                     iy + 11], slopes_stack[:, ix,
                                                            iy - 1 + 11],
                        slopes_stack[:, ix - 1,
                                     iy - 1 + 11], slopes_stack[:, ix - 1,
                                                                iy + 11]
                ]), axis=0)

        if actuator_response_df is None:
            actuator_response_df = pd.DataFrame(
                    actuator_response[:, ix,
                                      iy], index=np.round(amplitude_range, 3),
                    columns=[str(ix) + '_' + str(iy)])
        else:
            actuator_response_df = pd.concat([
                    actuator_response_df,
                    pd.DataFrame(actuator_response[:, ix, iy], index=np.round(
                            amplitude_range, 3),
                                 columns=[str(ix) + '_' + str(iy)])
            ], axis=1)

    return actuator_response, actuator_response_df, slopes_stack, amplitude_range


def _set_fps_floatvalue(fps_name, key, value):
    # TODO implement
    fps = toolbox.open_fps_once(fps_name, shm_and_fps_cache)

    if fps is None:
        message = f'ERROR: {fps_name} is missing'
        print(message)
        database.store_obs_log({'ao_log': message, 'obs_log': message})

        return -1

    rValue = fps.set_param(key, value)

    return rValue


def _set_fps_intvalue(fps_name, key, value):
    # TODO implement
    fps = toolbox.open_fps_once(fps_name, shm_and_fps_cache)

    if fps is None:
        message = f'ERROR: {fps_name} is missing'
        print(message)
        database.store_obs_log({'ao_log': message, 'obs_log': message})

        return -1

    rValue = fps.set_param(key, value)

    return rValue


def _set_emgain_tmux(emgain=1):
    server = libtmux.Server()

    try:
        session = server.find_where({"session_name": "nuvu_ctrl"})
    except:
        # TODO specify more precise exception
        session = False

    # If tmux session exists send query temperatures
    if session:
        session.attached_pane.send_keys(f'\ncam.SetEMCalibratedGain({emgain})')


def _set_exptime_tmux(exptime=0):
    server = libtmux.Server()

    try:
        session = server.find_where({"session_name": "nuvu_ctrl"})
    except:
        # TODO specify more precise exception
        session = False

    # If tmux session exists send query temperatures
    if session:
        session.attached_pane.send_keys(f'\nSetExposureTime({exptime})')


def _set_emgain_fps(emgain=1):
    _set_fps_intvalue('nuvu_acquire-1', 'emgain', str(emgain))


def _set_exptime_fps(exptime=0):
    _set_fps_floatvalue('nuvu_acquire-1', 'exposuretime', str(exptime))
