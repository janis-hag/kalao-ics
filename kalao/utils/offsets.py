import math
import time

import numpy as np

from kalao import logger
from kalao.cacao import toolbox
from kalao.hardware import calibunit
from kalao.interfaces import etcs

from kalao.definitions.enums import ReturnCode

import config


def camera_to_calibunit(dy: float) -> ReturnCode:
    position = calibunit.get_position()

    new_position = position + config.Offsets.camera_y_to_calibunit_mm * dy

    if math.isclose(calibunit.move(new_position), new_position, abs_tol=0.1):
        return ReturnCode.OK
    else:
        return ReturnCode.GENERIC_ERROR


def camera_to_telescope(dx: float, dy: float, gain: float = 1) -> ReturnCode:
    alt_offset = dx * config.Offsets.camera_x_to_tel_alt * gain
    az_offset = dy * config.Offsets.camera_y_to_tel_az * gain

    if etcs.send_altaz_offset(alt_offset, az_offset,
                              wait=True) == ReturnCode.OK:
        return ReturnCode.OK
    else:
        return ReturnCode.GENERIC_ERROR


def wfs_to_telescope(dx: float, dy: float, gain: float = 1) -> ReturnCode:
    alt_offset = dy * config.Offsets.wfs_y_to_tel_alt * gain
    az_offset = dx * config.Offsets.wfs_x_to_tel_az * gain

    # logger.info(
    #     'ttm',
    #     f'Offloading WFS tip-tilt to telescope. On WFS: dx={dx}px, dy={dy}px. Offloaded: alt={alt_offset}asec, az={az_offset}asec'
    # )

    if etcs.send_altaz_offset(alt_offset, az_offset,
                              wait=True) == ReturnCode.OK:
        return ReturnCode.OK
    else:
        return ReturnCode.GENERIC_ERROR


def camera_to_ttm(dx: float, dy: float, gain: float = 1,
                  output_stream: str = config.SHM.TTM_CENTERING) -> ReturnCode:
    ttm_shm = toolbox.get_shm(output_stream)

    if ttm_shm is None:
        logger.error('ttm', f'{output_stream} is missing')
        return ReturnCode.GENERIC_ERROR

    tip, tilt = ttm_shm.get_data(check=False)

    new_tip = tip + dx * config.Offsets.camera_x_to_ttm_tip * gain
    new_tilt = tilt + dy * config.Offsets.camera_y_to_ttm_tilt * gain

    new_tip, new_tilt = _check_ttm_saturation(new_tip, new_tilt)

    # logger.info(
    #     'ttm',
    #     f'Changing tip-tilt based on FLI. On FLI: tip={dx}px, tilt={dy}px. TTM set to: tip={new_tip}mrad, tilt={new_tilt}mrad'
    # )

    ttm_shm.set_data(np.array([new_tip, new_tilt]), True)

    time.sleep(1)

    return ReturnCode.OK


def wfs_to_ttm(dx: float, dy: float, gain: float = 1,
               output_stream: str = config.SHM.TTM_CENTERING) -> ReturnCode:
    ttm_shm = toolbox.get_shm(output_stream)

    if ttm_shm is None:
        logger.error('ttm', f'{output_stream} is missing')
        return ReturnCode.GENERIC_ERROR

    tip, tilt = ttm_shm.get_data(check=False)

    new_tip = tip + dy * config.Offsets.wfs_y_to_ttm_tip * gain
    new_tilt = tilt + dx * config.Offsets.wfs_x_to_ttm_tilt * gain

    new_tip, new_tilt = _check_ttm_saturation(new_tip, new_tilt)

    # logger.info(
    #     'ttm',
    #     f'Changing tip-tilt based on WFS. On WFS: dx={dx}px, dy={dy}px. TTM set to: tip={new_tip}mrad, tilt={new_tilt}mrad'
    # )

    ttm_shm.set_data(np.array([new_tip, new_tilt]), True)

    time.sleep(1)

    return ReturnCode.OK


def _check_ttm_saturation(tip: float, tilt: float) -> tuple[float, float]:
    if tip > 2.45:
        logger.warn('ttm', 'TTM saturated, limiting tip to 2.45')
        tip = 2.45
    elif tip < -2.45:
        logger.warn('ttm', 'TTM saturated, limiting tip to -2.45')
        tip = -2.45

    if tilt > 2.45:
        logger.warn('ttm', 'TTM saturated, limiting tilt to 2.45')
        tilt = 2.45
    elif tilt < -2.45:
        logger.warn('ttm', 'TTM saturated, limiting tilt to -2.45')
        tilt = -2.45

    return tip, tilt
