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

from kalao.utils import database, database_updater, kalao_time, file_handling
from configparser import ConfigParser
from pathlib import Path


config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')

# Read config file
parser = ConfigParser()
parser.read(config_path)

ScienceDataStorage = parser.get('FLI', 'ScienceDataStorage')
TemporaryDataStorage = parser.get('FLI', 'TemporaryDataStorage')

address = parser.get('FLI','IP')
port = parser.get('FLI','Port')

# check if config value format is right
if port.isdigit():
    # Converting int to string
    port = str(port)
else:
    print("Error: wrong values format for 'Port' in kalao.config file ")
    # return

def take_science_exposure(dit=0.05, filepath=None):

    req_result = take_image(dit, filepath)

    return req_result


def take_image(dit=0.05, filepath=None):

    if dit < 0:
        database.store_obs_log({'fli_log': 'Abort before exposure started.'})
        return 0

    # TODO move to file_handling (54-57)
    if filepath is None:
        file_handling.create_night_folder()
        filename = 'tmp_KALAO.' + kalao_time.get_isotime() + '.fits'
        filename = kalao_time.get_start_of_night() + os.sep + filename
        filepath = TemporaryDataStorage+os.sep+filename

    # Store monitoring status at start of exposure
    database_updater.update_plc_monitoring()
    params = {'exptime': dit, 'filepath': filepath}
    req = send_request('acquire', params)

    # Logging exposure command into database
    log(req)
    log_temporary_image_path(filepath)

    if req.status_code == 200:
        return 0
    else:
        return req.text


def log(req):
   database.store_obs_log({'fli_log': req.text+' ('+str(req.status_code)+')'})


def log_last_image_path( fli_image_path):
    database.store_obs_log({'fli_last_image_path': fli_image_path})


def log_temporary_image_path( fli_image_path):
    database.store_obs_log({'fli_temporary_image_path': fli_image_path})


def cancel():

    params = {'cancelExposure': True}
    req = send_request('cancelExposure', params)

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
