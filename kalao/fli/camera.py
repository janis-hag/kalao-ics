#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : camera.py
# @Date : 2021-03-18-10-02
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
camera.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

import requests
import requests.exceptions
import os
import json
from astropy.io import fits
from time import sleep

from kalao.utils import database, database_updater, file_handling
from configparser import ConfigParser
from pathlib import Path

from pyMilk.interfacing.isio_shmlib import SHM


config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')

# Read config file
parser = ConfigParser()
parser.read(config_path)

ScienceDataStorage = parser.get('FLI', 'ScienceDataStorage')
TemporaryDataStorage = parser.get('FLI', 'TemporaryDataStorage')
RequestTimeout = parser.getfloat('FLI', 'RequestTimeout')

address = parser.get('FLI', 'IP')
port = parser.get('FLI', 'Port')

# check if config value format is right
if port.isdigit():
    # Converting int to string
    port = str(port)
else:
    print("Error: wrong values format for 'Port' in kalao.config file ")
    # return


# Removing in order to only use take_image
# def take_science_exposure(dit=0.05, filepath=None):
#
#     req_result = take_image(dit, filepath, obscategory='SCIENCE')
#     if req_result == 0:
#         image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values'][0]
#         target_path_name = file_handling.save_tmp_image(image_path)
#
#         return target_path_name
#
#     else:
#         return req_result


def take_image(dit=0.05, filepath=None, header_keydict=None): # obs_category='TEST', obs_type='LAMP'):
    '''

    :param dit: Detector integration time to use
    :param filepath: Path where the file should be stored
    :return: path to the image
    '''

    if dit < 0:
        database.store_obs_log({'fli_log': 'Abort before exposure started.'})
        return 0

    if filepath is None:
        filepath = file_handling.create_night_filepath()

    # Store monitoring status at start of exposure
    database_updater.update_plc_monitoring()
    params = {'exptime': dit, 'filepath': filepath}
    req = send_request('acquire', params)

    # Logging exposure command into database
    log(req)
    log_temporary_image_path(filepath)

    if req.status_code == 200:

        image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values'][0]
        target_path_name = file_handling.save_tmp_image(image_path, header_keydict=header_keydict)

        return 0, target_path_name
    else:
        return req.text, None


def increment_image_counter():
    '''
    Increments the image counter by one

    :return: new image counter value
    '''
    image_count = database.get_latest_record('obs_log', key='fli_image_count')['fli_image_count'] +1
    database.store_obs_log({'fli_image_count': image_count})

    return image_count


def video_stream(dit=0.05):
   # initialise stream

    filepath = '/tmp/fli_image.fits'

    req = send_request('acquire', {'exptime': dit, 'filepath': filepath})

    img = fits.getdata(filepath)
    #img = cut_image(img)

    # Creating a brand new stream
    shm = SHM('fli_stream', img,
                 location=-1,  # CPU
                 shared=True,  # Shared
                 )

    while req.status_code == 200:
        req = send_request('acquire', {'exptime': dit, 'filepath': filepath})
        img = fits.getdata(filepath)

        #img = cut_image(img)
        shm.set_data(img)
        sleep(0.00001)


def log(req):
    database.store_obs_log({'fli_log': req.text+' ('+str(req.status_code)+')'})


def log_last_image_path(fli_image_path):
    database.store_obs_log({'fli_last_image_path': fli_image_path})


def log_temporary_image_path(fli_image_path):
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
    values = get_temperatures()
    database.store_monitoring(values)


def get_temperatures():

    req = send_request('temperature', 'GET')

    if req.status_code == 200:
        temperatures = json.loads(req.text)
        temperatures['fli_temp_CCD'] = temperatures.pop('ccd')
        temperatures['fli_temp_heatsink'] = temperatures.pop('heatsink')
        return temperatures

    return req.text


def set_temperature(temperature):

    params = {'temperature': temperature}
    req = send_request('temperature', params)

    if req.status_code == 200:
        return 0
    else:
        return req.text


def send_request(request_type, params):

    if request_type == 'acquire':
        increment_image_counter()
        database.store_obs_log({'sequencer_status': 'EXP'})

    url = 'http://'+address+':'+port+'/'+request_type
    if params == 'GET':
        req = requests.get(url, timeout=RequestTimeout)
    else:
        req = requests.post(url, json=params, timeout=RequestTimeout)

    return req


def initialise():
    # update fli file with content of kalao.config
    # systtemctl restart kalaocamera.service
    # https://github.com/torfsen/service
    return 0


def check_server_status():

    try:
        r = requests.get('http://'+address+':'+port+'/temperature')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return "DOWN"
    except requests.exceptions.HTTPError:
        return "ERROR"
    else:
        return "OK"
