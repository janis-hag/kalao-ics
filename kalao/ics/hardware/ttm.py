import numpy as np

from kalao.common.enums import ReturnCode

from kalao.ics import database, logger, memory
from kalao.ics.cacao import toolbox
from kalao.ics.interfaces import etcs

import config


def get_tiptilt(shm_name: str = config.SHM.TTM) -> tuple[float, float]:
    ttm_shm = toolbox.get_shm(shm_name)

    if ttm_shm is None:
        logger.error('ttm',
                     f'Can\'t get TTM tip and tilt, {shm_name} is missing')
        return np.nan, np.nan

    tip, tilt = ttm_shm.get_data(check=False)

    return tip, tilt


def set_tiptilt(shm_name: str, tip: float, tilt: float) -> tuple[float, float]:
    ttm_shm = toolbox.get_shm(shm_name)

    if ttm_shm is None:
        logger.error('ttm',
                     f'Can\'t set TTM tip and tilt, {shm_name} is missing')
        return np.nan, np.nan

    ttm_shm.set_data(np.array([tip, tilt]), True)

    return tip, tilt


def get_offloading() -> bool:
    return memory.hget('ttm', 'offloading', type=bool, default=True)


def set_offloading(state: bool) -> None:
    memory.hset('ttm', 'offloading', state)


def offload_to_telescope(gain: float = config.TTM.offload_gain,
                         threshold: float = config.TTM.offload_threshold,
                         override_threshold: bool = False,
                         input_stream: str = config.SHM.TTM) -> ReturnCode:
    """
    Offload current tip/tilt on the telescope by sending corresponding alt/az offsets.
    The gain can be adjusted to set how much of the tip/tilt should be offloaded.

    :return:
    """

    if not get_offloading():
        return ReturnCode.OK

    ttm_shm = toolbox.get_shm(input_stream)

    if ttm_shm is None:
        logger.error('ttm', f'{input_stream} is missing')
        return ReturnCode.GENERIC_ERROR

    tip, tilt = ttm_shm.get_data(check=False)

    to_offload = np.sqrt(tip**2 + tilt**2)

    if override_threshold or to_offload > threshold:
        alt_offload = tip * config.Offsets.ttm_tip_to_tel_alt * gain
        az_offload = tilt * config.Offsets.ttm_tilt_to_tel_az * gain

        # Keep offsets within defined range
        alt_offload = np.clip(alt_offload, -config.TTM.max_tel_offload,
                              config.TTM.max_tel_offload)
        az_offload = np.clip(az_offload, -config.TTM.max_tel_offload,
                             config.TTM.max_tel_offload)

        database.store(
            'obs', {
                'telescope_offload_altitude': alt_offload,
                'telescope_offload_azimut': az_offload
            })

        logger.info(
            'ttm',
            f'Offloading tip-tilt to telescope. On TTM: tip={tip}mrad, tilt={tilt}mrad. Offloaded: alt={alt_offload}asec, az={az_offload}asec'
        )

        etcs.send_altaz_offset(alt_offload, az_offload)

    return ReturnCode.OK


def check_saturation(tip: float, tilt: float) -> tuple[float, float]:
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
