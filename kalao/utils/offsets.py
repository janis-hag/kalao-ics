import time

import numpy as np

from kalao import logger
from kalao.cacao import toolbox
from kalao.interfaces import etcs
from kalao.plc import calibunit

import config


def fli_to_calibunit(dy):
    position = calibunit.get_position()

    new_position = position + config.Offsets.fli_y_to_calibunit_mm * dy

    calibunit.move(new_position)

    return 0


def fli_to_telescope(dx, dy, gain=1):
    alt_offset = dx * config.Offsets.fli_x_to_tel_alt * gain
    az_offset = dy * config.Offsets.fli_y_to_tel_az * gain

    etcs.send_altaz_offset(alt_offset, az_offset, wait=True)

    return 0


def wfs_to_telescope(dx, dy, gain=1):
    alt_offset = dy * config.Offsets.nuvu_y_to_tel_alt * gain
    az_offset = dx * config.Offsets.nuvu_x_to_tel_az * gain

    # logger.info(
    #     'ttm',
    #     f'Offloading WFS tip-tilt to telescope. On WFS: dx={dx}px, dy={dy}px. Offloaded: alt={alt_offset}asec, az={az_offset}asec'
    # )

    etcs.send_altaz_offset(alt_offset, az_offset, wait=True)

    return 0


def fli_to_ttm(dx, dy, gain=1, output_stream=config.Streams.TTM_CENTERING):
    ttm_stream = toolbox.open_stream_once(output_stream)

    if ttm_stream is None:
        logger.error('ttm', f'{output_stream} is missing')
        return -1

    tip, tilt = ttm_stream.get_data(check=False)

    new_tip = tip + dx * config.Offsets.fli_x_to_ttm_tip * gain
    new_tilt = tilt + dy * config.Offsets.fli_y_to_ttm_tilt * gain

    new_tip, new_tilt = check_ttm_saturation(new_tip, new_tilt)

    # logger.info(
    #     'ttm',
    #     f'Changing tip-tilt based on FLI. On FLI: tip={dx}px, tilt={dy}px. TTM set to: tip={new_tip}mrad, tilt={new_tilt}mrad'
    # )

    ttm_stream.set_data(np.array([new_tip, new_tilt]), True)

    time.sleep(1)

    return 0


def wfs_to_ttm(dx, dy, gain=1, output_stream=config.Streams.TTM_CENTERING):
    ttm_stream = toolbox.open_stream_once(output_stream)

    if ttm_stream is None:
        logger.error('ttm', f'{output_stream} is missing')
        return -1

    tip, tilt = ttm_stream.get_data(check=False)

    new_tip = tip + dy * config.Offsets.nuvu_y_to_ttm_tip * gain
    new_tilt = tilt + dx * config.Offsets.nuvu_x_to_ttm_tilt * gain

    new_tip, new_tilt = check_ttm_saturation(new_tip, new_tilt)

    # logger.info(
    #     'ttm',
    #     f'Changing tip-tilt based on WFS. On WFS: dx={dx}px, dy={dy}px. TTM set to: tip={new_tip}mrad, tilt={new_tilt}mrad'
    # )

    ttm_stream.set_data(np.array([new_tip, new_tilt]), True)

    time.sleep(1)

    return 0


def check_ttm_saturation(tip, tilt):
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


def offload_ttm_to_telescope(gain=config.TTM.offload_gain,
                             threshold=config.TTM.offload_threshold,
                             override_threshold=False,
                             input_stream=config.Streams.TTM):
    """
    Offload current tip/tilt on the telescope by sending corresponding alt/az offsets.
    The gain can be adjusted to set how much of the tip/tilt should be offloaded.

    :return:
    """

    ttm_stream = toolbox.open_stream_once(input_stream)

    if ttm_stream is None:
        logger.error('ttm', f'{input_stream} is missing')
        return -1

    tip, tilt = ttm_stream.get_data(check=False)

    to_offload = np.sqrt(tip**2 + tilt**2)

    if override_threshold or to_offload > threshold:
        alt_offload = tip * config.Offsets.ttm_tip_to_tel_alt * gain
        az_offload = tilt * config.Offsets.ttm_tilt_to_tel_az * gain

        # Keep offsets within defined range
        alt_offload = np.clip(alt_offload, -config.TTM.max_tel_offload,
                              config.TTM.max_tel_offload)
        az_offload = np.clip(az_offload, -config.TTM.max_tel_offload,
                             config.TTM.max_tel_offload)

        logger.info(
            'ttm',
            f'Offloading tip-tilt to telescope. On TTM: tip={tip}mrad, tilt={tilt}mrad. Offloaded: alt={alt_offload}asec, az={az_offload}asec'
        )

        etcs.send_altaz_offset(alt_offload, az_offload)

    return 0
