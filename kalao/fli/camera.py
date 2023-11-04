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
import json
import shutil
from unittest.mock import Mock

import numpy as np

from astropy.io import fits

import requests
import requests.exceptions
from requests.models import Response

from kalao.cacao import toolbox
from kalao.utils import database, database_updater, file_handling
from sequencer import system

import kalao_config as config
from kalao_enums import CameraServerStatus, SequencerStatus

fli_stream = toolbox.open_or_create_stream('fli_stream', (1024, 1024),
                                           np.uint16)


def take_frame(dit, filepath=None, nbflushes=None, do_not_log=False,
               update_stream=True):
    if filepath is None:
        filepath = '/tmp/fli_frame.fits'

    params = {'exptime': dit, 'filepath': filepath, 'nbflushes': nbflushes}
    req = _send_request('acquire', params, do_not_log=do_not_log)

    if req.status_code == 200:
        img = fits.getdata(filepath)

        if update_stream:
            if fli_stream.shape == img.shape:
                fli_stream.set_data(img, True)
            else:
                print("fli_stream not updated, shapes are inconsistent")

        return img, req
    else:
        return None, req


def take_cube(dit, nbframes, filepath=None, nbflushes=None, do_not_log=False,
              update_stream=True):
    if filepath is None:
        filepath = '/tmp/fli_cube.fits'

    params = {
            'exptime': dit,
            'nbframes': nbframes,
            'filepath': filepath,
            'nbflushes': nbflushes
    }
    req = _send_request('acquireCube', params, do_not_log=do_not_log)

    if req.status_code == 200:
        img_cube = fits.getdata(filepath)

        if update_stream:
            if fli_stream.shape == img_cube.shape[-1]:
                fli_stream.set_data(img_cube.shape[-1], True)
            else:
                print("fli_stream not updated, shapes are inconsistent")

        return img_cube, req
    else:
        return None, req


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

    if dit <= 0.001:
        database.store_obs_log({
                f'fli_log':
                        'Abort before exposure started. {dit=} below min value 0.001'
        })
        return -1, None

    if filepath is None:
        # Generate filename including path
        filepath = file_handling.create_night_filepath()

    # Store monitoring status at start of exposure
    database_updater.update_plc_monitoring()

    _, req = take_frame(dit, filepath=filepath)

    if get_temperatures(
    )['fli_temp_CCD'] > config.FLI.temperature_warn_threshold:
        message = 'WARN: CCD temperature above threshold: ' + str(
                get_temperatures()['fli_temp_CCD'])
        print(message)
        database.store_obs_log({'fli_log': message})

    # Logging exposure command into database
    log_request(req)
    log_temporary_image_path(filepath)

    if req.status_code == 200:
        image_path = database.get_latest_record_value('obs_log', 'fli_temporary_image_path')
        target_path_name = file_handling.save_tmp_image(
                image_path, sequencer_arguments=sequencer_arguments)

        return 0, target_path_name
    else:
        return req.text, None


def take_target(dit=0.05, seq_args=None, filepath=None):
    """
    Convenience function to interactively execute a target observation.

    :param dit: detector integration time in seconds.
    :param seq_args: dictionary of sequencer arguments.
    :param filepath:
    :return:
    """

    seq_args = {'type': 'K_TRGOBS'}

    rValue, image_path = take_image(dit=dit, filepath=None,
                                    sequencer_arguments=seq_args)

    return rValue, image_path


def take_dark(dit=0.05, seq_args=None, filepath=None):
    """
    Convenience function to interactively execute a dark exposure.

    :param dit:  detector integration time in seconds.
    :param seq_args: dictionary of sequencer arguments.
    :param filepath:
    :return:
    """
    seq_args = {'type': 'K_DARK'}

    rValue, image_path = take_image(dit=dit, filepath=None,
                                    sequencer_arguments=seq_args)

    return rValue, image_path


def increment_image_counter():
    """
    Increments the image counter by one

    :return: new image counter value
    """

    image_count = database.get_latest_record_value('obs_log',
                                                   key='fli_image_count') + 1
    database.store_obs_log({'fli_image_count': image_count})

    return image_count


def cut_image(img, window=None, center=None):

    if window is not None:
        hw = window // 2
        if center is None:
            c = [img.shape[0] // 2, img.shape[1] // 2]
        else:
            c = center
        img = img[c[0] - hw:c[0] + hw, c[1] - hw:c[1] + hw]

    img = img.astype(float)

    return img


def log_request(req):
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

    req = _send_request('temperature')

    if req.status_code == 200:
        temperatures = json.loads(req.text)
        temperatures['fli_temp_CCD'] = temperatures.pop('ccd')
        temperatures['fli_temp_heatsink'] = temperatures.pop('heatsink')
        return temperatures
    elif req.status_code == 503:
        temperatures = {'fli_temp_CCD': 0, 'fli_temp_heatsink': 0}
        return temperatures

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


def _send_request(request_type, params={}, do_not_log=False):
    # Clean params
    for key, value in list(params.items()):
        if value is None:
            del params[key]

    if not check_server_status() == CameraServerStatus.UP:
        req = Mock(spec=Response)
        req.json.return_value = {}
        req.text = 'Camera server down'
        # 503 Service Unavailable
        req.status_code = 503

    else:
        if request_type == 'acquire' and not do_not_log:
            increment_image_counter()
            database.store_obs_log({'sequencer_status': SequencerStatus.EXP})
            if 'exptime' in params.keys():
                database.store_obs_log({'fli_texp': params['exptime']})

        if config.FLI.dummy_camera:
            if request_type == 'acquire':
                shutil.copy(config.FLI.dummy_image_path, params['filepath'])

            req = Mock(spec=Response)
            req.text = 'Dummy image loaded'
            req.status_code = 200

        else:
            url = 'http://' + config.FLI.ip + ':' + str(
                    config.FLI.port) + '/' + request_type
            if params == {}:
                req = requests.get(url, timeout=config.FLI.request_timeout)
            else:
                req = requests.post(url, json=params,
                                    timeout=config.FLI.request_timeout)

    return req


def initialise():
    # TODO update fli file with content of kalao.config
    system.camera_service('restart')

    return 0


def check_server_status():
    """
    Verify if the camera server is up and running and check if the camera can be queried.

    :return: status of the camera server (UP/DOWN/ERROR)
    """

    server_status = system.camera_service('status')

    if server_status[0] == 'inactive':
        return CameraServerStatus.DOWN

    try:
        r = requests.get('http://' + config.FLI.ip + ':' +
                         str(config.FLI.port) + '/temperature')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return CameraServerStatus.DOWN
    except requests.exceptions.HTTPError:
        return CameraServerStatus.ERROR
    else:
        return CameraServerStatus.UP
