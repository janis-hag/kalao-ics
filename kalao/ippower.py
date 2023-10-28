#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import requests

from kalao.utils import database

from kalao_enums import IPPowerStatus
import kalao_config as config

def switch_ippower(power_port, status):
    """
    Function to switch an ippower port between ON and OFF

    :param power_port: port number
    :param status: IPPowerStatus.ON or IPPowerStatus.OFF
    :return: return code of the switching
    """

    params = {'components': 50947, 'cmd': 1, 'p': power_port, 's': int(status)}

    req = requests.get(config.IPPower.url, params=params)

    if req.status_code == 200:
        return status
    else:
        error_message = f'Could not switch camera IP-power for port {power_port} to {status}. HTTP-response: {req.text}  ({req.status_code})'
        database.store_obs_log({'obs_log': error_message})
        print(error_message)
        return -1


def ippower_status(power_port):
    """
    Check the ippower status of the power.

    :param power_port: port number
    :return: 0=OFF, 1=ON, -1=Error
    """

    params = {'components': 50947}

    req = requests.get(config.IPPower.url, params=params)

    if req.status_code == 200:
        state = req.json()['outputs'][power_port-1]['state']

        if state in [0, 1]:
            return IPPowerStatus(state)

    error_message = f'Could not get camera IP-power status for port {power_port}. HTTP-response: {req.text}  ({req.status_code})'
    database.store_obs_log({'obs_log': error_message})
    print(error_message)

    return -1
