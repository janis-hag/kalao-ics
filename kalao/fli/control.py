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
import requests.exceptions
import os

from kalao.utils import database, kalao_time
from configparser import ConfigParser
import os

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')

# Read config file
parser = ConfigParser()
parser.read(config_path)

ScienceDataStorage = parser.get('FLI','ScienceDataStorage')
TemporaryDataStorage = parser.get('FLI','Temporary')

#  TODO read from config
address = '127.0.0.1'
port = '9080'

def take_science_exposure(dit=0.05, filepath=None):

    req_result = take_image(dit, filepath)

    return req_result


def take_image(dit=0.05, filepath=None):

    if filepath is None:
        filename = 'tmp_KALAO.' + kalao_time.get_isotime() + '.fits'
        filepath = TemporaryDataStorage+os.sep+filename
    params = {'exptime': dit, 'filepath': filepath}
    req = send_request('acquire', params)

    # Logging exposure command into database
    log(req)
    database.store_obs_log({'fli_temporary_image_path': filepath})

    if req.status_code == 200:
        return 0
    else:
        return req.text


def log(req):
   database.store_obs_log({'fli_log': req.text+' ('+req.status_code+')'})


def log_last_image_path( fli_image_path):
    database.store_obs_log({'fli_last_image_path': fli_image_path})


def log_temporary_image_path( fli_image_path):
    database.store_obs_log({'fli_temporary_image_path': fli_image_path})


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
    database.store_monitoring(values)


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

    url = 'http://'+address+':'+port+'/'+type
    if params == 'GET':
        req = requests.get(url)
    else:
        req = requests.post(url, json = params)

    return req


def initialise():
    # update fli file with content of kalao.config
    # systtemctl restart kalaocamera.service
    # https://github.com/torfsen/service
    return 0

def check_server_status():

    try:
        r = requests.get('http://'+address+port)
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return "DOWN"
    except requests.exceptions.HTTPError:
        return "ERROR"
    else:
        return "OK"