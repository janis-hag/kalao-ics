import subprocess
import time
from pathlib import Path

import libtmux

from kalao.common.enums import ReturnCode
from kalao.common.rprint import rprint

from kalao.ics import database, logger
from kalao.ics.cacao import toolbox

import config


def start(start_nuvu_acquire: bool = True,
          start_shwfs_process: bool = True) -> ReturnCode:
    logger.info('wfs', 'Starting WFS')

    shwfs_process_fps = toolbox.get_fps(config.FPS.SHWFS)
    nuvu_acquire_fps = toolbox.get_fps(config.FPS.NUVU)

    subprocess.run([
        'python', '/home/kalao/kalao-camstack/camstack/cam_mains/main.py',
        'KALAOCAM'
    ])

    logger.info('wfs', 'Waiting for nuvu_raw to start')

    if toolbox.wait_file('/tmp/milk/nuvu_raw.im.shm') != ReturnCode.OK:
        logger.error('wfs', 'Timeout while waiting for nuvu_raw')
        return ReturnCode.GENERIC_ERROR

    if nuvu_acquire_fps is not None and start_nuvu_acquire:
        if not nuvu_acquire_fps.run_isrunning():
            logger.info('wfs', f'Starting {config.FPS.NUVU}')

            nuvu_acquire_fps.run_start()

            time.sleep(config.AO.wait_fps_run)

        if not nuvu_acquire_fps.run_isrunning():
            logger.error('wfs', f'Unable to start {config.FPS.NUVU}')
            return ReturnCode.GENERIC_ERROR

    if shwfs_process_fps is not None and start_shwfs_process:
        if not shwfs_process_fps.run_isrunning():
            logger.info('wfs', f'Starting {config.FPS.SHWFS}')

            shwfs_process_fps.run_start()

            time.sleep(config.AO.wait_fps_run)

        if not shwfs_process_fps.run_isrunning():
            logger.error('wfs', f'Unable to start {config.FPS.SHWFS}')
            return ReturnCode.GENERIC_ERROR

    return ReturnCode.OK


def stop() -> ReturnCode:
    logger.info('wfs', 'Stopping WFS')

    shwfs_process_fps = toolbox.get_fps(config.FPS.SHWFS)
    nuvu_acquire_fps = toolbox.get_fps(config.FPS.NUVU)

    if shwfs_process_fps is not None:
        if shwfs_process_fps.run_isrunning():
            logger.info('wfs', f'Stopping {config.FPS.SHWFS}')

            shwfs_process_fps.run_stop()

    if nuvu_acquire_fps is not None:
        if nuvu_acquire_fps.run_isrunning():
            logger.info('wfs', f'Stopping {config.FPS.NUVU}')

            nuvu_acquire_fps.run_stop()

    server = libtmux.Server()

    try:
        session = server.sessions.get(session_name='kalaocam_ctrl')
        pane = session.attached_pane
        pane.send_keys('C-c', enter=False)
        pane.send_keys('close()', enter=True)
        time.sleep(10)
        pane.send_keys('C-c', enter=False)
        pane.send_keys('C-z', enter=False)
        pane.send_keys('kill %', enter=True)
        session.kill_session()
    except (libtmux.exc.TmuxObjectDoesNotExist,
            libtmux._internal.query_list.ObjectDoesNotExist):
        pass

    Path('/tmp/milk/nuvu_raw.im.shm').unlink(missing_ok=True)

    return ReturnCode.OK


def acquisition_running() -> bool:
    nuvu_raw_shm = toolbox.get_shm(config.SHM.NUVU_RAW)

    if nuvu_raw_shm is None:
        return False

    return time.time() - nuvu_raw_shm.get_keywords(
    )['_MAQTIME'] / 1e6 < config.WFS.acquisition_time_timeout


def start_acquisition() -> ReturnCode:
    nuvu_raw_shm = toolbox.get_shm(config.SHM.NUVU_RAW)

    if nuvu_raw_shm is None:
        return ReturnCode.GENERIC_ERROR

    # Check if already running
    if acquisition_running():
        return ReturnCode.OK

    logger.info('wfs', 'Starting WFS acquisition')

    # Prevent inactivity checks from turning WFS off immediately
    database.store('obs', {'deadman_keepalive': -1})
    time.sleep(1)

    toolbox.set_tmux_value('kalaocam_ctrl', 'SetContinuousAcquisition')

    time.sleep(config.WFS.acquisition_start_wait)

    if not acquisition_running():
        logger.info('wfs', 'Failed to start WFS acquisition')
        return ReturnCode.GENERIC_ERROR

    return ReturnCode.OK


def stop_acquisition() -> ReturnCode:
    logger.info('wfs', 'Stopping WFS acquisition')

    toolbox.set_tmux_value('kalaocam_ctrl', 'AbortAcquisition')

    time.sleep(config.WFS.acquisition_start_wait)

    if acquisition_running():
        logger.info('wfs', 'Failed to stop WFS acquisition')
        return ReturnCode.GENERIC_ERROR

    return ReturnCode.OK


def set_temperature(temperature: float) -> float:
    return toolbox.set_tmux_value('kalaocam_ctrl', 'SetCCDTemperature',
                                  temperature)


def open_shutter() -> float:
    logger.info('wfs', 'Opening WFS shutter')

    return toolbox.set_tmux_value('kalaocam_ctrl', 'SetShutterMode', 2)


def close_shutter() -> float:
    logger.info('wfs', 'Closing WFS shutter')

    return toolbox.set_tmux_value('kalaocam_ctrl', 'SetShutterMode', -2)


def set_autogain_setting(setting: int) -> int | None:
    setting = int(setting)

    if setting > config.WFS.max_autogain_setting:
        setting = config.WFS.max_autogain_setting
    elif setting < 0:
        setting = 0

    return toolbox.set_fps_value(config.FPS.NUVU, 'autogain_setting', setting)


def set_emgain(emgain: int = 1, method: str = 'fps') -> int | None:
    """
    Set the EM gain of the Nuvu WFS camera.

    :param emgain: EM gain to set. 1 by default for no gain.
    :return:
    """

    if emgain < config.WFS.min_emgain:
        emgain = config.WFS.min_emgain
    elif emgain > config.WFS.max_emgain:
        emgain = config.WFS.max_emgain

    if method == 'fps':
        return toolbox.set_fps_value(config.FPS.NUVU, 'emgain', emgain)
    elif method == 'tmux':
        return toolbox.set_tmux_value('kalaocam_ctrl', 'SetEMCalibratedGain',
                                      emgain)
    else:
        logger.error('ao', f'Unknown method {method} in set_emgain')
        return -1


def set_exptime(exptime: float = 0, method: str = 'fps') -> float | None:
    """
    Set the exposure time of the Nuvu WFS camera.

    :param exptime: exposure time to set in milliseconds. 0 by default for highest frame rate.
    :return:
    """

    if exptime < config.WFS.min_exposuretime:
        exptime = config.WFS.min_exposuretime
    elif exptime > config.WFS.max_exposuretime:
        exptime = config.WFS.max_exposuretime

    if method == 'fps':
        return toolbox.set_fps_value(config.FPS.NUVU, 'exposuretime', exptime)
    elif method == 'tmux':
        return toolbox.set_tmux_value('kalaocam_ctrl', 'SetExposureTime',
                                      exptime)
    else:
        logger.error('ao', f'Unknown method {method} in set_exptime')
        return -1


def emgain_off() -> ReturnCode:
    """
    Completely turn of EM gain on the WFS camera. For double safety the command is sent directly to the tmux as well as
    to the nuvu_acquire fps.

    :return: 0 on success
    """

    ret = ReturnCode.OK

    try:
        toolbox.set_fps_value(config.FPS.NUVU, 'autogain_on', False)
        toolbox.set_fps_value(config.FPS.NUVU, 'autogain_setting', 0)
    except Exception as exc:
        rprint(
            f'Can\'t turn off autogain, {config.FPS.NUVU} seems not to be running.'
        )
        rprint(Exception, exc)
        ret = ReturnCode.GENERIC_ERROR

    try:
        toolbox.set_fps_value(config.FPS.NUVU, 'emgain', 1)
    except Exception as exc:
        rprint(
            f'Can\'t turn off emgain, {config.FPS.NUVU} seems not to be running.'
        )
        rprint(Exception, exc)
        ret = ReturnCode.GENERIC_ERROR

    try:
        toolbox.set_tmux_value('kalaocam_ctrl', 'SetEMCalibratedGain', 1)
    except Exception as exc:
        rprint(
            'Can\'t turn off emgain, kalaocam_ctrl seems not to be running.')
        rprint(Exception, exc)
        ret = ReturnCode.GENERIC_ERROR

    return ret


def optimize_flux() -> ReturnCode:
    # Check if we are already good
    if check_flux():
        return ReturnCode.OK

    nuvu_acquire_fps = toolbox.get_fps(config.FPS.NUVU)

    if nuvu_acquire_fps is None:
        logger.error('wfs', f'{config.FPS.NUVU} is missing')
        return ReturnCode.GENERIC_ERROR

    nuvu_acquire_fps.set_param('autogain_on', True)

    timeout = time.monotonic() + config.WFS.flux_stabilization_timeout

    prev_setting = -1
    prev_timestamp = time.monotonic()

    while time.monotonic() < timeout:
        setting = nuvu_acquire_fps.get_param('autogain_setting')
        timestamp = time.monotonic()

        if setting != prev_setting:
            prev_setting = setting
            prev_timestamp = timestamp

        elif timestamp - prev_timestamp >= config.WFS.flux_stabilization_time:
            if check_flux():
                return ReturnCode.OK
            else:
                break

    # Reset values if no signal detected
    nuvu_acquire_fps.set_param('autogain_setting', 0)
    set_emgain(1)
    set_exptime(0)

    return ReturnCode.TIMEOUT


def check_flux() -> bool:
    shwfs_fps = toolbox.get_fps(config.FPS.SHWFS)

    if shwfs_fps is None or not shwfs_fps.run_isrunning():
        return False

    flux_avg = 0.0
    for _ in range(config.WFS.flux_averaging):
        flux_avg += shwfs_fps.get_param('flux_avg')
        time.sleep(config.WFS.flux_averaging_interval)

    return flux_avg / config.WFS.flux_averaging > config.WFS.flux_min
