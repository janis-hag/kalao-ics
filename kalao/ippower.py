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
        power_port = get_port_number(power_port)

    logger.info('ippower', f'Switching port {power_port} to {state}')

    params = {'components': 50947, 'cmd': 1, 'p': power_port, 's': int(state)}
    req = requests.get(config.IPPower.url, params=params)

    if req.status_code == 200:
        new_state = req.json()['outputs'][power_port - 1]['state']

        if new_state in [0, 1]:
            return IPPowerStatus(new_state)

    logger.error(
        'ippower',
        f'Could not switch IPPower for port {power_port} to {state}. HTTP-response: {req.text}  ({req.status_code})'
    )
    return IPPowerStatus.ERROR


def status(power_port: str | int) -> IPPowerStatus:
    """
    Check the ippower status of the power.

    :param power_port: port number
    :return: IPPowerStatus or ReturnCode
    """

    req = requests.get(config.IPPower.url, params={'components': 50947})

    if isinstance(power_port, str):
        power_port = _get_port_number_from_req(req, power_port)

    if req.status_code == 200:
        state = req.json()['outputs'][power_port - 1]['state']

        if state in [0, 1]:
            return IPPowerStatus(state)

    logger.error(
        'ippower',
        f'Could not get IPPower status for port {power_port}. HTTP-response: {req.text}  ({req.status_code})'
    )
    return IPPowerStatus.ERROR


def get_port_number(power_port: str) -> int:
    req = requests.get(config.IPPower.url, params={'components': 50947})

    return _get_port_number_from_req(req, power_port)


def _get_port_number_from_req(req: requests.Response, power_port: str) -> int:
    if req.status_code == 200:
        return next((i + 1 for i, v in enumerate(req.json()['outputs'])
                     if v['name'] == power_port), -1)

    logger.error(
        'ippower',
        f'Could not contact IPPower to get port number. HTTP-response: {req.text}  ({req.status_code})'
    )
    return -1


def get_port_name(power_port: int) -> str:
    req = requests.get(config.IPPower.url, params={'components': 50947})

    return _get_port_name_from_req(req, power_port)


def _get_port_name_from_req(req: requests.Response, power_port: int) -> str:
    if req.status_code == 200:
        if 0 < power_port <= len(req.json()['outputs']):
            return req.json()['outputs'][power_port - 1]['name']
        else:
            return ''

    logger.error(
        'ippower',
        f'Could not contact IPPower to get port name. HTTP-response: {req.text}  ({req.status_code})'
    )
    return ''


def status_all() -> dict[str, IPPowerStatus]:
    return {
        'ippower_rtc_status': status(config.IPPower.Port.RTC),
        'ippower_bench_status': status(config.IPPower.Port.Bench),
        'ippower_dm_status': status(config.IPPower.Port.DM),
    }


def init() -> ReturnCode:
    # Do not change state of PC or DM

    # Powering up the bench
    if switch(config.IPPower.Port.Bench, IPPowerStatus.ON) == IPPowerStatus.ON:
        return ReturnCode.IPPOWER_OK
    else:
        return ReturnCode.IPPOWER_ERROR
