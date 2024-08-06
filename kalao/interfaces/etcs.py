import time
from typing import Any

import numpy as np
import pandas as pd

import requests
import requests.exceptions

from kalao import logger

from kalao.definitions.enums import ETCSServerStatus, ReturnCode

import config

# To test:
# curl --header "Content-Type: application/json" --header "Authorization: ETCS_API_TOKEN_2023" http://10.10.132.102:10002/axis/status | jq


def get_tracking() -> bool:
    ret, resp = _send_request('GET', '/tracking/status')

    if ret == ReturnCode.ETCS_OK:
        return resp['tracking']['b_trackingOn']
    else:
        return False


def get_instrument() -> int:
    ret, resp = _send_request('GET', '/m3/status')

    if ret == ReturnCode.ETCS_OK:
        return resp['instrument']
    else:
        return -1


def get_altaz() -> tuple[float, float]:
    ret, resp = _send_request('GET', '/axis/status')

    if ret == ReturnCode.ETCS_OK:
        if resp['homing']['azi']['b_homed']:
            azimut = resp['positions']['azi']
        else:
            azimut = np.nan

        if resp['homing']['ele']['b_homed']:
            altitude = resp['positions']['ele']
        else:
            altitude = np.nan

        return altitude, azimut
    else:
        return np.nan, np.nan


def send_altaz_offset(delta_alt_arcsec: float, delta_az_arcsec: float,
                      wait: bool = True) -> ReturnCode:
    """
    Send altitude azimuth offset to ETCS telescope server.

    :param delta_alt_arcsec: altitude offset to apply
    :param delta_az_arcsec: azimuth offset to apply
    :return:
    """

    logger.info(
        'etcs',
        f'Sending offsets of {delta_alt_arcsec}" in altitude and {delta_az_arcsec}" in azimut'
    )

    params = {'az_arcsec': delta_az_arcsec, 'el_arcsec': delta_alt_arcsec}

    ret, resp = _send_request('POST', '/tracking/offset', params)

    if wait:
        time.sleep(2)

    return ret


def get_focus() -> float:
    ret, resp = _send_request('GET', '/m2/status')

    if ret == ReturnCode.ETCS_OK:
        return resp['z']
    else:
        return np.nan


def set_focus(position: float, wait: bool = True) -> float:
    """
    Send focus offset to the ETCS telescope server. Values can either be interpreted as relative offsets if with a
    leading +/-, or absolute if the value is only a number.

    :param focus_offset: absolute or relative focus offset to apply
    :return:
    """

    # if new_position > 35000 or new_position < 25000:
    #     logger.error('etcs', f'set_focus value out of bounds: {new_position}')
    #     return -1

    logger.info('etcs', f'Moving focus position to {position} µm')

    params = {'position': position}

    ret, resp = _send_request('POST', '/m2/focus', params)

    if wait:
        time.sleep(5)

    return get_focus()


def get_tube_temps() -> dict[str, int | float]:
    temps = pd.read_csv(config.ETCS.temperature_file, sep='\t',
                        header=0).iloc[-1]

    return {
        'tunix': int(temps.tunix),
        'temttb': float(temps.temttb),
        'temtth': float(temps.temtth),
    }


def set_m3_lin(position: float) -> ReturnCode:
    params = {"position": position}

    ret, resp = _send_request('POST', '/m3/position/lin', params)

    return ret  # TODO: return lin pos


def set_m3_rot(position: float) -> ReturnCode:
    params = {"position": position}

    ret, resp = _send_request('POST', '/m3/position/rot', params)

    return ret  # TODO: return rot pos


def _send_request(method: str, endpoint: str, params: dict[str, Any] |
                  None = None) -> tuple[ReturnCode, Any]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": config.ETCS.token
    }

    kwargs = {}
    if method == 'POST' and params is not None:
        kwargs['json'] = params

    try:
        req = requests.request(
            method, f'http://{config.ETCS.host}:{config.ETCS.port}{endpoint}',
            timeout=config.ETCS.request_timeout, headers=headers, **kwargs)

        req.raise_for_status()

        if req.headers.get('content-type', '').startswith('application/json'):
            return ReturnCode.ETCS_OK, req.json()
        else:
            return ReturnCode.ETCS_OK, req.text

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return ReturnCode.ETCS_SERVER_UNREACHABLE, None

    except requests.exceptions.HTTPError:
        if req.headers.get('content-type', '').startswith('application/json'):
            text = req.json()["message"]
        else:
            text = req.text

        logger.error(
            'etcs',
            f'Telescope server endpoint {endpoint} answered with an Error {req.status_code}, {text}'
        )
        return ReturnCode.ETCS_ERROR, None


def server_status() -> ETCSServerStatus:
    try:
        r = requests.get(f'http://{config.ETCS.host}:{config.ETCS.port}/ping')
        r.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return ETCSServerStatus.DOWN
    except requests.exceptions.HTTPError:
        return ETCSServerStatus.ERROR
    else:
        return ETCSServerStatus.UP
