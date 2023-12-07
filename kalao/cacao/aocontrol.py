#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : com_tools.py
# @Date : 2022-06-13-09-51
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
aocontrol.py is part of the KalAO Instrument Control Software (KalAO-ICS).
"""

import subprocess
import time

import numpy as np

from kalao import ippower
from kalao.cacao import toolbox
from kalao.utils import database, kalao_tools

import libtmux

from tcs_communication import t120

from kalao.definitions.enums import IPPowerStatus, LoopStatus

import config

shm_and_fps_cache = {}


def close_loops():
    """
    Close the primary DM AO loop followed by the secondary TTM loop.

    :return:
    """

    return switch_loops(close=True)


def open_loops():
    """
    Open the primary DM AO loop followed by the secondary TTM loop.

    :return:
    """

    return switch_loops(close=False)


def switch_loops(close=True):
    """
    Toggle the loop value of the primary DM AO loop and the secondary TTM loop.

    :return:
    """

    if close:
        database.store('obs', {'ao_log': 'Closing both loops'})
        loop_order = [config.AO.DM_loop_number, config.AO.TTM_loop_number]
    else:
        database.store('obs', {'ao_log': 'Opening both loops'})
        loop_order = [config.AO.TTM_loop_number, config.AO.DM_loop_number]

    for i in loop_order:
        switch_loop(i, close)

    return check_loops()


def close_loop(loop_number):
    return switch_loop(loop_number, close=True)


def open_loop(loop_number):
    return switch_loop(loop_number, close=False)


def switch_loop(loop_number, close=True):
    """
    Toggle the loop value of one loop

    :return:
    """

    if close:
        database.store('obs', {'ao_log': f'Closing loop {loop_number}'})
    else:
        database.store('obs', {'ao_log': f'Opening loop {loop_number}'})

    fps_mfilt = toolbox.open_fps_once(f"mfilt-{loop_number}",
                                      shm_and_fps_cache)

    if fps_mfilt is None:
        database.store('obs',
                       {'ao_log': f'[ERROR] mfilt-{loop_number} is missing'})

        return LoopStatus.ERROR

    fps_mfilt.set_param('loopON', close)

    if not close:
        fps_mfilt.set_param('loopZERO', True)

    time.sleep(1)

    if loop_number == 1:
        ret = autogain_switch(on=close)

        if ret != 0:
            return ret  #TODO

    return check_loops()


def check_loops():
    status = LoopStatus(0)

    fps_mfilt1 = toolbox.open_fps_once("mfilt-1", shm_and_fps_cache)

    if fps_mfilt1 is not None and fps_mfilt1.get_param('loopON'):
        status |= LoopStatus.DM_LOOP_ON

    fps_mfilt2 = toolbox.open_fps_once("mfilt-2", shm_and_fps_cache)

    if fps_mfilt2 is not None and fps_mfilt2.get_param('loopON'):
        status |= LoopStatus.TTM_LOOP_ON

    return status


def autogain_on():
    return autogain_switch(on=True)


def autogain_off():
    return autogain_switch(on=False)


def autogain_switch(on=True):
    nuvu_fps = toolbox.open_fps_once(config.FPS.NUVU, shm_and_fps_cache)

    if nuvu_fps is not None:
        nuvu_fps.set_param('autogain_on', on)
        return 0

    return -1


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

    mgainfact_stream = toolbox.open_stream_once(stream_name, shm_and_fps_cache)

    mode = int(np.floor(mode))

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

    ret = -1

    try:
        fps = toolbox.open_fps_once(config.FPS.NUVU, shm_and_fps_cache)

        if fps is not None:
            fps.set_param('autogain_on', False)
            fps.set_param('autogain_setting', 0)
    except Exception as err:
        print(
            f'Can\'t turn off autogain, {config.FPS.NUVU} seems not to be running.'
        )
        print(Exception, err)

    try:
        _set_emgain_fps(emgain=1)
        ret = 0
    except Exception as err:
        print(
            f'Can\'t turn off emgain, {config.FPS.NUVU} seems not to be running.'
        )
        print(Exception, err)

    try:
        _set_emgain_tmux(emgain=1)
        ret = 0
    except Exception as err:
        print(f'Can\'t turn off emgain, nucu_ctrl seems not to be running.')
        print(Exception, err)

    return ret


def set_emgain(emgain=1, method='tmux'):
    """
    Set the EM gain of the Nuvu WFS camera.

    :param emgain: EM gain to set. 1 by default for no gain.
    :return:
    """

    emgain = int(emgain)

    if emgain > config.WFS.max_emgain:
        emgain = config.WFS.max_emgain
    elif emgain < 1:
        emgain = 1

    if method == 'fps':
        _set_emgain_fps(emgain)
    elif method == 'tmux':
        _set_emgain_tmux(emgain)
    else:
        database.store('obs', {
            'ao_log': f'[ERROR] Unknown method {method} in set_emgain'
        })


def set_exptime(exptime=0, method='tmux'):
    """
    Set the exposure time of the Nuvu WFS camera.

    :param exptime: exposure time to set in milliseconds. 0 by default for highest frame rate.
    :return:
    """

    if exptime < config.WFS.min_exposuretime:
        exptime = config.WFS.min_exposuretime

    if method == 'fps':
        _set_exptime_fps(exptime)
    elif method == 'tmux':
        _set_exptime_tmux(exptime)
    else:
        database.store('obs', {
            'ao_log': f'[ERROR] Unknown method {method} in set_exptime'
        })


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

    mgainfact_stream = toolbox.open_stream_once(stream_name, shm_and_fps_cache)

    if mgainfact_stream is not None:
        mgainfact_array = mgainfact_stream.get_data(check=False)

        if not keep_existing_flat:
            mgainfact_array = np.ones(len(mgainfact_array))

        if cut_off > len(mgainfact_array):
            # cut_off frequency has to be within the range of modes. If higher all values will be set to 1
            cut_off = len(mgainfact_array)

        if last_mode is None:
            last_mode = len(mgainfact_array)  # -1
        elif last_mode + 1 < cut_off:
            last_mode = cut_off
            mgainfact_array[last_mode + 1:] = 0
        elif last_mode > len(mgainfact_array):
            last_mode = len(mgainfact_array)
        else:
            mgainfact_array[last_mode + 1:] = 0

        if not cut_off == last_mode:
            # down = np.linspace(1, 0, len(mgainfact_array) - cut_off + 2 - (len(mgainfact_array) - last_mode) )[1:-1]
            down = np.linspace(1, 0, last_mode - cut_off + 2)[1:-1]
            mgainfact_array[cut_off:last_mode] = down

        mgainfact_stream.set_data(mgainfact_array, True)

        return 0

    else:
        return -1


def tip_tilt_offload_ttm_to_telescope(gain=config.TTM.offload_gain,
                                      override_threshold=False,
                                      input_stream=config.Streams.TTM,
                                      port=config.T120.port):
    """
    Offload current tip/tilt on the telescope by sending corresponding alt/az offsets.
    The gain can be adjusted to set how much of the tip/tilt should be offloaded.

    :param gain: Gain factor, set to 0.25 by default.
    :return:
    """

    ttm_stream = toolbox.open_stream_once(input_stream, shm_and_fps_cache)

    if ttm_stream is None:
        database.store('obs',
                       {'ttm_log': f'[ERROR] {input_stream} is missing'})
        return -1

    tip, tilt = ttm_stream.get_data(check=False)

    to_offload = np.sqrt(tip**2 + tilt**2)

    if override_threshold or to_offload > config.TTM.offload_threshold:
        alt_offload = tip * config.TTM.tip_to_onsky * gain
        az_offload = tilt * config.TTM.tilt_to_onsky * gain

        # Keep offsets within defined range
        alt_offload = np.clip(alt_offload, -config.TTM.max_tel_offload,
                              config.TTM.max_tel_offload)
        az_offload = np.clip(az_offload, -config.TTM.max_tel_offload,
                             config.TTM.max_tel_offload)

        database.store(
            'obs', {
                'ttm_log':
                    f'Offloading tip-tilt to telescope. Current: tip={tip}mrad, tilt={tilt}mrad. Offload: alt={alt_offload}asec, az={az_offload}asec'
            })

        t120.send_altaz_offset(alt_offload, az_offload, port=port)

    return 0


def tip_tilt_offset_fli_to_ttm(x_tip, y_tilt, absolute=False,
                               output_stream=config.Streams.TTM_CENTERING):
    """
    Moves the tip tilt mirror by sending an offset in mrad. The value as input is given in pixels and converted.

    :param x_tip: number of pixels to tip
    :param y_tilt: number of pixels to tilt
    :param absolute: Flag to indicate that tip tilt values are in absolute radian. By default, set to False.
    :param output_stream: name of the stream to use to set the offset.

    :return:
    """

    ttm_stream = toolbox.open_stream_once(output_stream, shm_and_fps_cache)

    if ttm_stream is None:
        database.store('obs',
                       {'ttm_log': f'[ERROR] {output_stream} is missing'})
        return -1

    tip, tilt = ttm_stream.get_data(check=False)

    # TIP
    if absolute:
        new_tip = x_tip
    else:
        new_tip = tip + x_tip * config.AO.FLI_tip_to_TTM

    # TILT
    if absolute:
        new_tilt = y_tilt
    else:
        new_tilt = tilt + y_tilt * config.AO.FLI_tilt_to_TTM

    new_tip, new_tilt = check_ttm_saturation(new_tip, new_tilt)

    database.store(
        'obs', {
            'ttm_log':
                f'Changing tip-tilt based on FLI. Current: tip={x_tip}px, tilt={y_tilt}px. New: tip={new_tip}mrad, tilt={new_tilt}mrad'
        })

    ttm_stream.set_data(np.array([new_tip, new_tilt]), True)

    return 0


def tip_tilt_wfs_to_ttm(tt_threshold=config.AO.WFS_centering_slope_threshold,
                        output_stream=config.Streams.TTM_CENTERING):
    """
    Precise tip/tilt centering on the wavefront sensor.

    :param tt_threshold: precision at which the centering need to be based on the residual slope.
    :return:
    """

    tip_centered = False
    tilt_centered = False

    ttm_stream = toolbox.open_stream_once(output_stream, shm_and_fps_cache)
    slopes_fps = toolbox.open_fps_once(config.FPS.SHWFS, shm_and_fps_cache)

    if ttm_stream is None:
        database.store('obs',
                       {'ttm_log': f'[ERROR] {output_stream} is missing'})
        return -1

    if slopes_fps is None:
        database.store('obs',
                       {'ttm_log': f'[ERROR] {config.FPS.SHWFS} is missing'})
        return -1

    # TODO verify that shwfs enough illuminated for centering

    timeout_time = time.monotonic() + config.Starfinder.centering_timeout

    while not (tip_centered and tilt_centered):
        if time.monotonic() > timeout_time:
            database.store('obs', {
                'ttm_log': '[ERROR] Timeout during centering using WFS'
            })

            return -1

        tip, tilt = ttm_stream.get_data(check=False)

        tip_residual = slopes_fps.get_param('slope_y')
        tilt_residual = slopes_fps.get_param('slope_x')

        if np.abs(tip_residual) < tt_threshold:
            tip_centered = True
            new_tip = tip
        else:
            new_tip = tip + tip_residual * config.AO.WFS_tip_to_TTM

        if np.abs(tilt_residual) < tt_threshold:
            tilt_centered = True
            new_tilt = tilt
        else:
            new_tilt = tilt + tilt_residual * config.AO.WFS_tilt_to_TTM

        new_tip, new_tilt = check_ttm_saturation(new_tip, new_tilt)

        database.store(
            'obs', {
                'ttm_log':
                    f'Changing tip-tilt based on WFS. Current: tip={tip_residual}px, tilt={tilt_residual}px. New: tip={new_tip}mrad, tilt={new_tilt}mrad'
            })

        ttm_stream.set_data(np.array([new_tip, new_tilt]), True)

        time.sleep(1)

    return 0


def check_ttm_saturation(tip, tilt):
    if tip > 2.45:
        database.store('obs', {
            'ttm_log': '[WARNING] TTM saturated, limiting tip to 2.45'
        })
        tip = 2.45
    elif tip < -2.45:
        database.store('obs', {
            'ttm_log': '[WARNING] TTM saturated, limiting tip to -2.45'
        })
        tip = -2.45

    if tilt > 2.45:
        database.store('obs', {
            'ttm_log': '[WARNING] TTM saturated, limiting tilt to 2.45'
        })
        tilt = 2.45
    elif tilt < -2.45:
        database.store('obs', {
            'ttm_log': '[WARNING] TTM saturated, limiting tilt to -2.45'
        })
        tilt = -2.45

    return tip, tilt


def optimize_wfs_flux():
    nuvu_acquire_fps = toolbox.open_fps_once(config.FPS.NUVU,
                                             shm_and_fps_cache)

    if nuvu_acquire_fps is None:
        database.store('obs',
                       {'ao_log': f'[ERROR] {config.FPS.NUVU} is missing'})
        return -1

    # Check if we are already good
    if check_wfs_flux():
        return 0

    nuvu_acquire_fps.set_param('autogain_setting', 0)

    for setting in range(config.WFS.max_autogain_setting):
        nuvu_acquire_fps.set_param('autogain_setting', setting)

        time.sleep(nuvu_acquire_fps.get_param('autogain_wait') / 1000)

        for i in range(10):
            if check_wfs_flux():
                return 0

    # Reset values if no signal detected
    nuvu_acquire_fps.set_param('autogain_setting', 0)
    set_emgain(1)
    set_exptime(0)

    return -1


def check_wfs_flux():
    slopes_flux_stream = toolbox.open_stream_once(config.Streams.FLUX,
                                                  shm_and_fps_cache)

    if slopes_flux_stream is None:
        database.store('obs',
                       {'ao_log': '[ERROR] shwfs_slopes_flux is missing'})
        return -1

    slopes_flux = slopes_flux_stream.get_data(check=True)

    illuminated_fraction = kalao_tools.wfs_illumination_fraction(
        slopes_flux, config.AO.WFS_illumination_threshold,
        config.AO.fully_illuminated_subaps)

    return illuminated_fraction > config.AO.WFS_illumination_fraction


def turn_dm_on():

    bmc_display_fps = toolbox.open_fps_once(config.FPS.BMC, shm_and_fps_cache)

    if ippower.status(config.IPPower.Port.BMC_DM) == IPPowerStatus.OFF:
        database.store('obs', {'dm_log': 'Powering on DM ippower'})

        # Avoid safety turning DM off immediately
        time.sleep(1)

        ret = ippower.switch(config.IPPower.Port.BMC_DM, IPPowerStatus.ON)

        if ret != IPPowerStatus.ON:
            return -1

        time.sleep(config.Timers.dm_wait_between_actions)

    if bmc_display_fps is not None:
        if not bmc_display_fps.run_runs():
            database.store('obs', {'dm_log': f'Starting {config.FPS.BMC}'})

            # Avoid safety turning DM off immediately
            time.sleep(1)

            bmc_display_fps.run_start()

            time.sleep(config.Timers.dm_wait_between_actions)

            reset_dm(config.AO.DM_loop_number)

        if not bmc_display_fps.run_runs():
            database.store('obs',
                           {'dm_log': f'Unable to start {config.FPS.BMC}'})

            return -1

    return 0


def turn_dm_off():
    database.store('obs', {'dm_log': 'Turning off DM'})

    bmc_display_fps = toolbox.open_fps_once(config.FPS.BMC, shm_and_fps_cache)

    database.store('obs', {'dm_log': 'Resetting DM'})
    reset_dm(config.AO.DM_loop_number)

    time.sleep(config.Timers.dm_wait_between_actions)

    if bmc_display_fps is not None:
        database.store('obs', {'dm_log': f'Stopping {config.FPS.BMC}'})
        bmc_display_fps.run_stop()

        time.sleep(config.Timers.dm_wait_between_actions)

    database.store('obs', {'dm_log': 'Powering off DM ippower'})
    ret = ippower.switch(config.IPPower.Port.BMC_DM, IPPowerStatus.OFF)

    if ret == IPPowerStatus.OFF:
        return 0
    else:
        return -1


def restart_wfs():
    shwfs_process_fps = toolbox.open_fps_once(config.FPS.SHWFS,
                                              shm_and_fps_cache)
    nuvu_acquire_fps = toolbox.open_fps_once(config.FPS.NUVU,
                                             shm_and_fps_cache)

    shwfs_process_was_running = False
    nuvu_acquire_was_running = False

    if shwfs_process_fps is not None:
        if shwfs_process_fps.run_runs():
            shwfs_process_was_running = True

            database.store('obs', {'ao_log': f'Stopping {config.FPS.SHWFS}'})

            shwfs_process_fps.run_stop()

    if nuvu_acquire_fps is not None:
        if nuvu_acquire_fps.run_runs():
            nuvu_acquire_was_running = True

            database.store('obs', {'ao_log': f'Stopping {config.FPS.NUVU}'})

            nuvu_acquire_fps.run_stop()

    # TODO: delete stream

    subprocess.run(["/home/kalao/kalao-camstack/scripts/cam-nuvustart"])

    time.sleep(config.AO.wait_camstack_start)

    if nuvu_acquire_fps is not None and nuvu_acquire_was_running:
        if not nuvu_acquire_fps.run_runs():
            database.store('obs', {'ao_log': f'Starting {config.FPS.NUVU}'})

            nuvu_acquire_fps.run_start()

            time.sleep(config.AO.wait_fps_run)

        if not nuvu_acquire_fps.run_runs():
            database.store('obs',
                           {'ao_log': f'Unable to start {config.FPS.NUVU}'})

            return -1

    if shwfs_process_fps is not None and shwfs_process_was_running:
        if not shwfs_process_fps.run_runs():
            database.store('obs', {'ao_log': f'Starting {config.FPS.SHWFS}'})

            shwfs_process_fps.run_start()

            time.sleep(config.AO.wait_fps_run)

        if not shwfs_process_fps.run_runs():
            database.store('obs',
                           {'ao_log': f'Unable to start {config.FPS.SHWFS}'})

            return -1


def reset_channel(dm_number, channel, force_flat=False):
    log = 'ao_log'
    if dm_number == config.AO.DM_loop_number:
        log = 'dm_log'
    elif dm_number == config.AO.TTM_loop_number:
        log = 'ttm_log'

    database.store('obs', {
        log: f'Resetting channel {channel:02d} of DM {dm_number:02d}'
    })

    stream = f'dm{dm_number:02d}disp{channel:02d}'

    if stream == config.Streams.DM_LOOP:
        dm_fps = toolbox.open_fps_once(f"mfilt-{dm_number}", shm_and_fps_cache)
        if dm_fps is not None:
            database.store('obs', {log: f'Zeroing loop {dm_number}'})

            dm_fps.set_param('loopZERO', True)

    elif stream == config.Streams.TTM_LOOP:
        ttm_fps = toolbox.open_fps_once(f"mfilt-{dm_number}",
                                        shm_and_fps_cache)
        if ttm_fps is not None:
            database.store('obs', {log: f'Zeroing loop {dm_number}'})

            ttm_fps.set_param('loopZERO', True)

    elif stream == config.Streams.DM_FLAT and not force_flat:
        return 0

    stream = toolbox.open_stream_once(stream, shm_and_fps_cache)
    toolbox.zero_stream(stream)

    return 0


def reset_dm(dm_number):
    log = 'ao_log'
    if dm_number == config.AO.DM_loop_number:
        log = 'dm_log'
    elif dm_number == config.AO.TTM_loop_number:
        log = 'ttm_log'

    database.store('obs', {log: f'Resetting DM {dm_number:02d}'})

    for i in range(0, 12):
        reset_channel(dm_number, i)

    return 0


def reset_all_dms(max_dm_number=2):

    ret = 0

    for i in range(1, max_dm_number + 1):
        ret += reset_dm(i)

    return ret


def _set_fps_floatvalue(fps_name, key, value):
    fps = toolbox.open_fps_once(fps_name, shm_and_fps_cache)

    if fps is None:
        database.store('obs', {'ao_log': f'[ERROR] {fps_name} is missing'})

        return -1

    ret = fps.set_param(key, value)

    return ret


def _set_fps_intvalue(fps_name, key, value):
    fps = toolbox.open_fps_once(fps_name, shm_and_fps_cache)

    if fps is None:
        database.store('obs', {'ao_log': f'[ERROR] {fps_name} is missing'})

        return -1

    ret = fps.set_param(key, value)

    return ret


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
    _set_fps_intvalue(config.FPS.NUVU, 'emgain', str(emgain))


def _set_exptime_fps(exptime=0):
    _set_fps_floatvalue(config.FPS.NUVU, 'exposuretime', str(exptime))
