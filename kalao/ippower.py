#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""
from kalao import logger

import requests

from kalao.definitions.enums import IPPowerStatus, ReturnCode

import config


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


def status(power_port: str | int) -> IPPowerStatus:
    """
    Check the ippower status of the power.

    :param power_port: port number
    :return: IPPowerStatus or ReturnCode
    """

    req = _send_request()

    if isinstance(power_port, str):
        _power_port = _get_port_number_from_req(req, power_port)
    else:
        _power_port = power_port

    if req is not None and _power_port != -1:
        state = req.json()['outputs'][_power_port - 1]['state']

        if state in [0, 1]:
            return IPPowerStatus(state)

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


def status_all() -> dict[str, IPPowerStatus]:
    return {
        'ippower_rtc_status': status(config.IPPower.Port.RTC),
        'ippower_bench_status': status(config.IPPower.Port.Bench),
        'ippower_dm_status': status(config.IPPower.Port.DM),
    }


def init() -> ReturnCode:
    logger.info('ippower', 'Initialising IPPowers')

    # Do not change state of PC or DM

    # Powering up the bench
    if switch(config.IPPower.Port.Bench, IPPowerStatus.ON) == IPPowerStatus.ON:
        return ReturnCode.IPPOWER_OK
    else:
        return ReturnCode.IPPOWER_ERROR


def _send_request(params: dict = {}) -> requests.Response | None:
    _params = {'components': 50947}
    _params.update(params)

    try:
        req = requests.get(config.IPPower.url, params=_params)
    except requests.exceptions.RequestException as e:
        logger.error(
            'ippower',
            f'IPPower endpoint answered with a {e.__class__.__name__} exception.'
        )
        return None

    if req.status_code == 200:
        return req
    else:
        logger.error(
            'ippower',
            f'IPPower endpoint answered with an Error {req.status_code}: {req.text}'
        )
