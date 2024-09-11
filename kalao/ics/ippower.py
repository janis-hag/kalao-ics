#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""
import requests

from kalao.common.enums import IPPowerStatus, ReturnCode

from kalao.ics import logger

import config

mapping = {
    'ippower_rtc_status': config.IPPower.Port.RTC,
    'ippower_bench_status': config.IPPower.Port.Bench,
    'ippower_dm_status': config.IPPower.Port.DM,
}


def switch(power_port: str | int, state: IPPowerStatus) -> IPPowerStatus:
    """
    Function to switch an ippower port between ON and OFF

    :param power_port: port number
    :param state: IPPowerStatus.ON or IPPowerStatus.OFF
    :return: return code of the switching
    """

    if isinstance(power_port, str):
        _power_port = get_port_number(power_port)
    else:
        _power_port = power_port

    logger.info('ippower', f'Switching port {power_port} to {state}')

    req = _send_request({'cmd': 1, 'p': _power_port, 's': int(state)})

    if req is not None and _power_port != -1:
        new_state = req.json()['outputs'][_power_port - 1]['state']

        if new_state in [0, 1]:
            return IPPowerStatus(new_state)

    logger.error(
        'ippower',
        f'Could not switch IPPower for port {power_port} to {state}.')
    return IPPowerStatus.ERROR


def get_status(power_port: str | int) -> IPPowerStatus:
    """
    Check the ippower status of the power.

    :param power_port: port number
    :return: IPPowerStatus or ReturnCode
    """

    req = _send_request()

    return _get_port_status_from_req(req, power_port)


def get_all_status() -> dict[str, IPPowerStatus]:
    req = _send_request()

    data = {}
    for key, power_port in mapping.items():
        data[key] = _get_port_status_from_req(req, power_port)

    return data


def _get_port_status_from_req(req: requests.Response, power_port: str | int):
    if isinstance(power_port, str):
        _power_port = _get_port_number_from_req(req, power_port)
    else:
        _power_port = power_port

    if req is not None and _power_port != -1:
        state = req.json()['outputs'][_power_port - 1]['state']

        if state in [0, 1]:
            return IPPowerStatus(state)
        else:
            logger.error('ippower',
                         f'Invalid status {state} for {power_port}.')
            return IPPowerStatus.ERROR

    else:
        logger.error('ippower',
                     f'Could not get IPPower status for port {power_port}.')
        return IPPowerStatus.ERROR


def get_port_number(power_port: str) -> int:
    req = _send_request()

    return _get_port_number_from_req(req, power_port)


def _get_port_number_from_req(req: requests.Response, power_port: str) -> int:
    _power_port = -1

    if req is not None:
        _power_port = next((i + 1 for i, v in enumerate(req.json()['outputs'])
                            if v['name'] == power_port), -1)

    if _power_port != -1:
        return _power_port
    else:
        logger.error('ippower',
                     f'Cloud not find port number for port {power_port}')
        return -1


def get_port_name(power_port: int) -> str:
    req = _send_request()

    return _get_port_name_from_req(req, power_port)


def _get_port_name_from_req(req: requests.Response, power_port: int) -> str:
    if req is not None and 0 < power_port <= len(req.json()['outputs']):
        return req.json()['outputs'][power_port - 1]['name']
    else:
        logger.error('ippower',
                     f'Cloud not find port name for port {power_port}')
        return ''


def init() -> ReturnCode:
    logger.info('ippower', 'Initialising IPPowers')

    # Do not change state of RTC or DM

    # Powering up the bench
    if switch(config.IPPower.Port.Bench, IPPowerStatus.ON) == IPPowerStatus.ON:
        ret_init = ReturnCode.IPPOWER_OK
    else:
        ret_init = ReturnCode.IPPOWER_ERROR

    logger.info('ippower', 'IPPowers initialised')

    return ret_init


def _send_request(params: dict | None = None) -> requests.Response | None:
    _params = {'components': 50947}

    if params is not None:
        _params.update(params)

    try:
        req = requests.get(config.IPPower.url, params=_params)

        req.raise_for_status()

        return req

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.error('ippower', 'IPPower server seems to be down')
        return None

    except requests.exceptions.HTTPError:
        logger.error(
            'ippower',
            f'IPPower endpoint answered with an Error {req.status_code}, {req.text}'
        )
        return None
