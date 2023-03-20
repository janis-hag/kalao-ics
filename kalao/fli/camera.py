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
import shutil

import requests
import requests.exceptions
from requests.models import Response
from unittest.mock import Mock
import os
import json
from astropy.io import fits
from time import sleep
import numpy as np

from kalao.utils import database, database_updater, file_handling
from sequencer import system
from configparser import ConfigParser
from pathlib import Path

from pyMilk.interfacing.isio_shmlib import SHM

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')

# Read config file
parser = ConfigParser()
parser.read(config_path)

ScienceDataStorage = parser.get('FLI', 'ScienceDataStorage')
TemporaryDataStorage = parser.get('FLI', 'TemporaryDataStorage')
RequestTimeout = parser.getfloat('FLI', 'RequestTimeout')
DummyCamera = parser.getboolean('FLI', 'DummyCamera')
DummyImagePath = parser.get('FLI', 'DummyImagePath')
TemperatureWarnThreshold = parser.getfloat('FLI', 'TemperatureWarnThreshold')

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


def take_image(
        dit=0.05, filepath=None,
        sequencer_arguments=None):  # obs_category='TEST', obs_type='LAMP'):
    """

    :param sequencer_arguments:
    :param dit: Detector integration time to use
    :param filepath: Path where the file should be stored
    :return: path to the image
    """

    # TODO verify first with check_server_status() before sending request

    if dit < 0:
        database.store_obs_log({'fli_log': 'Abort before exposure started.'})
        return 0

    if filepath is None:
        # Generate filename including path
        filepath = file_handling.create_night_filepath()

    # Store monitoring status at start of exposure
    database_updater.update_plc_monitoring()

    params = {'exptime': dit, 'filepath': filepath}
    req = _send_request('acquire', params)

    if get_temperatures()['fli_temp_CCD'] > TemperatureWarnThreshold:
        message = 'WARN: CCD temperature above threshold: ' + str(
                get_temperatures()['fli_temp_CCD'])
        print(message)
        database.store_obs_log({'fli_log': message})

    # Logging exposure command into database
    log(req)
    log_temporary_image_path(filepath)

    if req.status_code == 200:

        image_path = database.get_obs_log([
                'fli_temporary_image_path'
        ], 1)['fli_temporary_image_path']['values'][0]
        target_path_name = file_handling.save_tmp_image(
                image_path, sequencer_arguments=sequencer_arguments)

        return 0, target_path_name
    else:
        return req.text, None


def take_dark(dit=0.05):
    # TODO add docstring

    seq_args = {'type': 'K_DARK', 'code': 'dark'}

    rValue, image_path = take_image(dit=dit, filepath=None,
                                    sequencer_arguments=seq_args)

    return rValue, image_path


def increment_image_counter():
    """
    Increments the image counter by one

    :return: new image counter value
    """

    image_count = database.get_latest_record(
            'obs_log', key='fli_image_count')['fli_image_count'] + 1
    database.store_obs_log({'fli_image_count': image_count})

    return image_count


def video_stream(dit=0.05, window=None, center=None):
    # TODO add docstring

    # initialise stream

    # TODO verify first with check_server_status() before sending request

    filepath = '/tmp/fli_image.fits'

    req = _send_request('acquire', {'exptime': dit, 'filepath': filepath})

    img = fits.getdata(filepath)

    if window is not None:
        img = cut_image(img, window=window, center=center)

    # Creating a brand-new stream
    shm = SHM(
            'fli_stream',
            img,
            location=-1,  # CPU
            shared=True,  # Shared
    )

    try:
        while req.status_code == 200:
            req = _send_request('acquire', {
                    'exptime': dit,
                    'filepath': filepath
            })
            img = fits.getdata(filepath)

            if window is not None:
                img = cut_image(img, window=window, center=center)

            shm.set_data(img)
            sleep(0.001)

    except KeyboardInterrupt:
        print('interrupted!')


def cut_image(img, window=None, center=None):

    if window is not None:
        hw = int(np.round(window / 2))
        if center is None:
            c = [img.shape[0] / 2, img.shape[1] / 2]
        else:
            c = center
        img = img[c[0] - hw:c[0] + hw, c[1] - hw:c[1] + hw]

    img = img.astype(float)

    return img


def log(req):
    # TODO add docstring

    database.store_obs_log({
            'fli_log': req.text + ' (' + str(req.status_code) + ')'
    })


def log_last_image_path(fli_image_path):
    # TODO add docstring

    database.store_obs_log({'fli_last_image_path': fli_image_path})


def log_temporary_image_path(fli_image_path):
    # TODO add docstring

    database.store_obs_log({'fli_temporary_image_path': fli_image_path})


def cancel():
    # TODO add docstring

    params = {'cancelExposure': True}
    req = _send_request('cancelExposure', params)

    if req.status_code == 200:
        return 0
    else:
        return req.text


def database_update():
    """
    Updates the monitoring database with the camera CCD and heatsink temperatures.

    :return:
    """

    # fli_temp_heatsink
    # fli_temp_CCD
    values = get_temperatures()
    database.store_monitoring(values)


def get_temperatures():
    """
    Gets CCD and heatsink temperatures from the camera.

    :return:
    """

    req = _send_request('temperature', 'GET')

    if req.status_code == 200:
        temperatures = json.loads(req.text)
        temperatures['fli_temp_CCD'] = temperatures.pop('ccd')
        temperatures['fli_temp_heatsink'] = temperatures.pop('heatsink')
        return temperatures
    elif req.status_code == 503:
        temperatures = {'fli_temp_CCD': 0, 'fli_temp_heatsink': 0}

    return req.text


def set_temperature(temperature):
    """
    Sets the CCD temperature.

    :param temperature:
    :return:
    """
    params = {'temperature': temperature}
    req = _send_request('temperature', params)

    if req.status_code == 200:
        return 0
    elif req.status_code == 503:
        return -1
    else:
        return req.text


def _send_request(request_type, params):

    if not check_server_status == 'OK':

        req = Mock(spec=Response)

        req.json.return_value = {}
        req.text = 'Camera server down'
        # 503 Service Unavailable
        req.status_code = 503

        # class Object(object):
        #     pass
        #
        # req = Object()
        # req.text = '-1'
        # req.status_code = 200

    else:
        if request_type == 'acquire':
            increment_image_counter()
            database.store_obs_log({'sequencer_status': 'EXP'})
            if 'exptime' in params.keys():
                database.store_obs_log({'fli_texp': params['exptime']})

        if DummyCamera:
            if request_type == 'acquire':
                shutil.copy(DummyImagePath, params['filepath'])

            class Object(object):
                pass

            req = Object()
            req.text = '-1'
            req.status_code = 200

        else:
            url = 'http://' + address + ':' + port + '/' + request_type
            if params == 'GET':
                req = requests.get(url, timeout=RequestTimeout)
            else:
                req = requests.post(url, json=params, timeout=RequestTimeout)

    return req


def poweroff():

    systemd_status = system.camera_service('STOP')
    ipp_switch_status = _switch_ippower('OFF')


def poweron():
    ipp_switch_status = _switch_ippower('ON')
    sleep(20)
    systemd_status = system.camera_service('RESTART')


def _switch_ippower(value):
    """
    Function to swithc the camera ippower port between ON and OFF

    TODO read the url and p parameter from kalao.config

    :param value: ON or OFF
    :return: return code the switching
    """

    url = 'http://10.10.132.94/statusjsn.js'

    params = {'components': 50947, 'cmd': 1, 'p': 7, 's': 0}

    if value == 'ON':
        params['s'] = 1
    elif not value == 'OFF':
        error_message = f'Unknow camer ippower switch value ({value})'
        database.store_obs_log({'fli_log': error_message})
        print(error_message)

        return -1

    req = requests.get(url, params=params)

    if req.status_code == 200:
        return 0
    else:
        error_message = f'Could not switch camera IP-power to {value}. HTTP-response: {req.text}  ({req.status_code})'
        database.store_obs_log({'fli_log': error_message})
        print(error_message)
        return -1


def initialise():
    # TODO update fli file with content of kalao.config
    system.camera_service('restart')

    return 0


def check_server_status():
    """
    Verify if the camera server is up and running and check if the camera can be queried.

    :return: status of the camera server (OK/DOWN/ERROR)
    """

    server_status = system.camera_service('status')

    if server_status[0] == 'inactive':
        return 'DOWN'

    try:
        r = requests.get('http://' + address + ':' + port + '/temperature')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return "DOWN"
    except requests.exceptions.HTTPError:
        return "ERROR"
    else:
        return "OK"
