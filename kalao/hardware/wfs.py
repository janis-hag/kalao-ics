import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from kalao import database, logger
from kalao.cacao import toolbox

import libtmux

from kalao.definitions.enums import ReturnCode

import config


def start(start_nuvu_acquire: bool = True,
          start_shwfs_process: bool = True) -> ReturnCode:
    logger.info('wfs', 'Starting WFS')

    shwfs_process_fps = toolbox.open_fps_once(config.FPS.SHWFS)
    nuvu_acquire_fps = toolbox.open_fps_once(config.FPS.NUVU)

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

    shwfs_process_fps = toolbox.open_fps_once(config.FPS.SHWFS)
    nuvu_acquire_fps = toolbox.open_fps_once(config.FPS.NUVU)

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
    except libtmux.exc.TmuxObjectDoesNotExist:
        pass

    Path('/tmp/milk/nuvu_raw.im.shm').unlink(missing_ok=True)

    return ReturnCode.OK


def acquisition_running() -> bool:
    nuvu_raw_shm = toolbox.open_shm_once(config.SHM.NUVU_RAW)

    if nuvu_raw_shm is None:
        return False

    maqtime = datetime.fromtimestamp(
        nuvu_raw_shm.get_keywords()['_MAQTIME'] / 1e6, tz=timezone.utc)
    return (datetime.now(timezone.utc) -
            maqtime).total_seconds() < config.WFS.acquisition_time_timeout


def start_acquisition() -> ReturnCode:
    nuvu_raw_shm = toolbox.open_shm_once(config.SHM.NUVU_RAW)

    if nuvu_raw_shm is None:
        return ReturnCode.GENERIC_ERROR

    # Check if already running
    if acquisition_running():
        return ReturnCode.OK

    logger.info('wfs', 'Starting WFS acquisition')

    # Prevent inactivity checks from turning WFS off immediately
    database.store('obs', {'deadman_keepalive': 0})
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
