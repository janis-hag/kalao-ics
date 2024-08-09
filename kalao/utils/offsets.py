import math
import time

import numpy as np

from kalao.hardware import calibunit, ttm
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

    if etcs.send_altaz_offset(alt_offset, az_offset,
                              wait=True) == ReturnCode.OK:
        return ReturnCode.OK
    else:
        return ReturnCode.GENERIC_ERROR


def camera_to_ttm(dx: float, dy: float, gain: float = 1,
                  output_shm_name: str = config.SHM.TTM_CENTERING
                  ) -> ReturnCode:
    tip, tilt = ttm.get_tiptilt(output_shm_name)

    if np.isnan(tip) or np.isnan(tilt):
        return ReturnCode.GENERIC_ERROR

    new_tip = tip + dx * config.Offsets.camera_x_to_ttm_tip * gain
    new_tilt = tilt + dy * config.Offsets.camera_y_to_ttm_tilt * gain

    new_tip, new_tilt = ttm.check_saturation(new_tip, new_tilt)

    if ttm.set_tiptilt(output_shm_name, new_tip,
                       new_tilt) != (new_tip, new_tilt):
        return ReturnCode.GENERIC_ERROR
    else:
        time.sleep(1)
        return ReturnCode.OK


def wfs_to_ttm(dx: float, dy: float, gain: float = 1,
               output_shm_name: str = config.SHM.TTM_CENTERING) -> ReturnCode:
    tip, tilt = ttm.get_tiptilt(output_shm_name)

    if np.isnan(tip) or np.isnan(tilt):
        return ReturnCode.GENERIC_ERROR

    new_tip = tip + dy * config.Offsets.wfs_y_to_ttm_tip * gain
    new_tilt = tilt + dx * config.Offsets.wfs_x_to_ttm_tilt * gain

    new_tip, new_tilt = ttm.check_saturation(new_tip, new_tilt)

    if ttm.set_tiptilt(output_shm_name, new_tip,
                       new_tilt) != (new_tip, new_tilt):
        return ReturnCode.GENERIC_ERROR
    else:
        time.sleep(0.1)
        return ReturnCode.OK
