#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : control.py
# @Date : 2021-03-18-10-02
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
control.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

import requests

from kalao.utils import database, kalao_time
#from datetime import datetime


def take_science_exposure(dit=0.05, filepath=None):

    req.result = acquire(dit,filepath)

    return req.result


def acquire(dit=0.05, filepath=None):

    if filepath is None:
        filename = 'KALAO.' + kalao_time.get_isotime() + '.fits'
        filepath = '/home/kalao/data/science/'+filename
    params = {'exptime': dit, 'filepath': filepath}
    req = send_request('acquire', params)
    # store to mongo db instead of printing.
    print(req.status_code)
    print(req.text)

    if req.status_code == 200:
        return 0
    else:
        return req.text


def cancel():

    params = {'cancel': True}
    req = send_request('cancel', params)

    if req.status_code == 200:
        return 0
    else:
        return req.text


def database_update():
    # fli_temp_heatsink
    # fli_temp_CCD
    values = {'fli_temp_CCD': get_temperature()}
    database.store_measurements(values)


def get_temperature():

    req = send_request('temperature', 'GET')

    if req.status_code == 200:
        temperature = req.text
        return temperature

    return req.text


def set_temperature(temperature):

    params = {'temperature': temperature}
    req = send_request('temperature', params)

    if req.status_code == 200:
        return 0
    else:
        return req.text


def send_request(type, params):

    url = 'http://127.0.0.1:9080/'+type
    if params == 'GET':
        req = requests.get(url)
    else:
        req = requests.post(url, json = params)

    return req


def initialise():
    # systtemctl restart kalaocamera.service
    return 0
