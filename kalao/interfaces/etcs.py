import json
import time

import numpy as np
import pandas as pd

from kalao import logger

import requests
import requests.exceptions

from kalao.definitions.enums import ETCSServerStatus, ReturnCode

import config

# To test:
# curl --header "Content-Type: application/json" --header "Authorization: ETCS_API_TOKEN_2023" http://10.10.132.102:10002/axis/status | jq


def get_tracking():
    ret, resp = _send_request('/tracking/status')

    if ret == ReturnCode.ETCS_OK:
        return resp['tracking']['b_trackingOn']
    else:
        return False


def get_instrument():
    ret, resp = _send_request('/m3/status')

    if ret == ReturnCode.ETCS_OK:
        return resp['instrument']
    else:
        return -1


def get_altaz():
    ret, resp = _send_request('/axis/status')

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


def send_altaz_offset(delta_alt_arcsec, delta_az_arcsec, wait=True):
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

    ret, resp = _send_request('tracking/offset', params)

    if wait:
        time.sleep(2)

    return ret


def get_focus():
    ret, resp = _send_request('/m2/status')

    if ret == ReturnCode.ETCS_OK:
        return resp['z']
    else:
        return np.nan


def set_focus(position, wait=True):
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

    params = {"position": position}

    ret, resp = _send_request('/m2/focus', params)

    if wait:
        time.sleep(5)

    return get_focus()


def get_tube_temps():
    temps = pd.read_csv(config.ETCS.temperature_file, sep='\t',
                        header=0).iloc[-1]

    return {
        'tunix': int(temps.tunix),
        'temttb': float(temps.temttb),
        'temtth': float(temps.temtth),
    }


def set_m3_lin(position):
    params = {"position": position}

    ret, resp = _send_request('/m3/position/lin', params)

    return ret


def set_m3_rot(position):
    params = {"position": position}

    ret, resp = _send_request('/m3/position/rot', params)

    return ret


def _send_request(endpoint, params={}):
    # Clean params
    for key, value in list(params.items()):
        if value is None:
            del params[key]

    if config.ETCS.dummy_telescope:
        return ReturnCode.ETCS_OK, {}

    else:
        headers = {
            "Content-Type": "application/json",
            "Authorization": config.ETCS.token
        }

        url = f'http://{config.ETCS.ip}:{config.ETCS.port}{endpoint}'

        try:
            if params == {}:
                req = requests.get(url, timeout=config.ETCS.request_timeout,
                                   headers=headers)
            else:
                req = requests.post(url, json=params,
                                    timeout=config.ETCS.request_timeout,
                                    headers=headers)
        except requests.exceptions.RequestException:
            return ReturnCode.ETCS_SERVER_DOWN, None

        try:
            data = json.loads(req.text)
        except Exception:
            data = req.text

        if req.status_code == 200:
            return ReturnCode.ETCS_OK, data
        else:
            text = ''

            if isinstance(data, dict):
                if data.get('message') is not None:
                    text += f' {data.get("message")}'
            else:
                text = f' {data}'

            logger.error(
                'etcs',
                f'Telescope server endpoint {endpoint} answered with an Error {req.status_code}.{text}'
            )

            return ReturnCode.ETCS_ERROR, data


def check_server_status():
    """
    Verify if the ETCS server is up and running and check if the camera can be queried.

    :return: status of the camera server (UP/DOWN/ERROR)
    """

    try:
        r = requests.get(f'http://{config.ETCS.ip}:{config.ETCS.port}/')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return ETCSServerStatus.DOWN
    except requests.exceptions.HTTPError:
        return ETCSServerStatus.ERROR
    else:
        return ETCSServerStatus.UP
