#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import requests


def switch_ippower(power_port, status):
    """
    Function to swithc the camera ippower port between ON and OFF

    TODO read the url and p parameter from kalao.config

    :param value: ON or OFF
    :return: return code the switching
    """

    params = {'components': 50947, 'cmd': 1, 'p': power_port, 's': int(status)}

    req = requests.get(config.IPPower.url, params=params)

    if req.status_code == 200:
        return 0
    else:
        error_message = f'Could not switch camera IP-power for port {power_port} to {value}. HTTP-response: {req.text}  ({req.status_code})'
        database.store_obs_log({'obs_log': error_message})
        print(error_message)
        return -1


def ippower_status(power_port):
    """
    Check the ippower status of the camera.

    :return: 0=OFF, 1=ON, -1=Error
    """

    params = {'components': 50947}

    req = requests.get(config.IPPower.url, params=params)

    if req.status_code == 200:

        state = req.json()['outputs'][power_port-1]['state']

        if state in [0, 1]:
            return state

    error_message = f'Could not get camera IP-power status for port {power_port}. HTTP-response: {req.text}  ({req.status_code})'
    database.store_obs_log({'obs_log': error_message})
    print(error_message)

    return -1
