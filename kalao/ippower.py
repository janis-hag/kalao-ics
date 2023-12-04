#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

from kalao.utils import database

import requests

from kalao.definitions.enums import IPPowerStatus

import config


def switch(power_port, state):
    """
    Function to switch an ippower port between ON and OFF

    :param power_port: port number
    :param state: IPPowerStatus.ON or IPPowerStatus.OFF
    :return: return code of the switching
    """

    database.store('obs',
                   {'ippower_log': f'Switching port {power_port} to {state}'})

    params = {'components': 50947, 'cmd': 1, 'p': power_port, 's': int(state)}
    req = requests.get(config.IPPower.url, params=params)

    if req.status_code == 200:
        new_state = req.json()['outputs'][power_port - 1]['state']

        if new_state in [0, 1]:
            return IPPowerStatus(new_state)

    database.store(
        'obs', {
            'ippower_log':
                f'Could not switch camera IP-power for port {power_port} to {state}. HTTP-response: {req.text}  ({req.status_code})'
        })
    return IPPowerStatus.ERROR


def status(power_port):
    """
    Check the ippower status of the power.

    :param power_port: port number
    :return: IPPowerStatus or ReturnCode
    """

    params = {'components': 50947}
    req = requests.get(config.IPPower.url, params=params)

    if req.status_code == 200:
        state = req.json()['outputs'][power_port - 1]['state']

        if state in [0, 1]:
            return IPPowerStatus(state)

    database.store(
        'obs', {
            'ippower_log':
                f'Could not get camera IP-power status for port {power_port}. HTTP-response: {req.text}  ({req.status_code})'
        })
    return IPPowerStatus.ERROR


def status_all():
    return {
        'ippower_bench_status': status(config.IPPower.Port.Bench),
        'ippower_dm_status': status(config.IPPower.Port.BMC_DM),
    }
