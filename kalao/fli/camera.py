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
import time

import numpy as np

from astropy.io import fits

from kalao import services
from kalao.cacao import toolbox
from kalao.timers import database as database_timer
from kalao.utils import database, file_handling

import requests
import requests.exceptions

from kalao.definitions.enums import (CameraServerStatus, ReturnCode,
                                     SequencerStatus)

import config

fli_stream = toolbox.open_or_create_stream('fli_stream', (1024, 1024),
                                           np.uint16)


def take_frame(dit, filepath=None, nbflushes=None, update_stream=True):
    if filepath is None:
        filepath = '/tmp/fli_frame.fits'

    params = {'exptime': dit, 'filepath': filepath, 'nbflushes': nbflushes}
    ret, _ = _send_request('acquire', params)

    if ret == ReturnCode.CAMERA_OK:
        img = fits.getdata(filepath)

        if update_stream:
            if fli_stream.shape == img.shape:
                fli_stream.set_data(img, True)
            else:
                print("fli_stream not updated, shapes are inconsistent")

        # TODO return req, img for coherence with other take_image or opposite

        return img
    else:
        return None


def take_cube(dit, nbframes, filepath=None, nbflushes=None,
              update_stream=True):
    if filepath is None:
        filepath = '/tmp/fli_cube.fits'

    params = {
        'exptime': dit,
        'nbframes': nbframes,
        'filepath': filepath,
        'nbflushes': nbflushes
    }
    ret, _ = _send_request('acquireCube', params)

    if ret == ReturnCode.CAMERA_OK:
        img_cube = fits.getdata(filepath)

        if update_stream:
            if fli_stream.shape == img_cube.shape[-1]:
                fli_stream.set_data(img_cube.shape[-1], True)
            else:
                print("fli_stream not updated, shapes are inconsistent")

        return img_cube
    else:
        return None


def take_image(
        dit=0.05, filepath=None,
        sequencer_arguments=None):  # obs_category='TEST', obs_type='LAMP'):
    """
    :param sequencer_arguments:
    :param dit: Detector integration time to use
    :param filepath: Path where the file should be stored
    :return: path to the image
    """

    if dit <= 0.001:
        database.store(
            'obs', {
                f'fli_log':
                    f'[ERROR] Abort before exposure started. DIT={dit} below min value 0.001'
            })
        return None

    if filepath is None:
        # Generate filename including path
        filepath = file_handling.generate_image_filepath()

    # Store monitoring status at start of exposure
    database_timer.update_monitoring_db()

    database.store('obs', {
        'sequencer_status': SequencerStatus.EXP,
        'fli_texp': dit
    })

    img = take_frame(dit, filepath=filepath)

    if img is not None:
        database.store('obs', {'fli_temporary_image_path': filepath})
        target_path_name = file_handling.save_tmp_image(
            filepath, sequencer_arguments=sequencer_arguments)

        return target_path_name
    else:
        return None


def take_target(dit=0.05, seq_args=None, filepath=None):
    """
    Convenience function to interactively execute a target observation.

    :param dit: detector integration time in seconds.
    :param seq_args: dictionary of sequencer arguments.
    :param filepath:
    :return:
    """

    seq_args = {'type': 'K_TRGOBS'}

    return take_image(dit=dit, filepath=None, sequencer_arguments=seq_args)


def take_dark(dit=0.05, seq_args=None, filepath=None):
    """
    Convenience function to interactively execute a dark exposure.

    :param dit:  detector integration time in seconds.
    :param seq_args: dictionary of sequencer arguments.
    :param filepath:
    :return:
    """
    seq_args = {'type': 'K_DARK'}

    return take_image(dit=dit, filepath=None, sequencer_arguments=seq_args)


def take_tech(dit=0.05, seq_args=None, filepath=None):
    """
    Convenience function to interactively execute a dark exposure.

    :param dit:  detector integration time in seconds.
    :param seq_args: dictionary of sequencer arguments.
    :param filepath:
    :return:
    """
    seq_args = {'type': 'K_TECH'}

    return take_image(dit=dit, filepath=None, sequencer_arguments=seq_args)


def increment_image_counter():
    """
    Increments the image counter by one

    :return: new image counter value
    """

    image_count = database.get_last_value('obs', 'fli_image_count')

    if image_count is None:
        image_count = 1
    else:
        image_count += 1

    database.store('obs', {'fli_image_count': image_count})

    return image_count


def cancel():
    # TODO add docstring

    ret, _ = _send_request('cancelExposure')

    return ret


def get_temperatures():
    """
    Gets CCD and heatsink temperatures from the camera.

    :return:
    """

    ret, temperatures = _send_request('temperature')

    if ret == ReturnCode.CAMERA_OK:
        temperatures['fli_temp_CCD'] = temperatures.pop('ccd')
        temperatures['fli_temp_HS'] = temperatures.pop('heatsink')
        return temperatures

    else:
        return {'fli_temp_CCD': np.inf, 'fli_temp_HS': np.inf}


def set_temperature(temperature):
    """
    Sets the CCD temperature.

    :param temperature:
    :return:
    """
    params = {'temperature': temperature}
    ret, _ = _send_request('temperature', params)
    return ret


def _send_request(request_type, params={}):
    # Clean params
    for key, value in list(params.items()):
        if value is None:
            del params[key]

    if not check_server_status() == CameraServerStatus.UP:
        return ReturnCode.CAMERA_SERVER_DOWN, {}

    else:
        if config.FLI.dummy_camera:
            if request_type == 'acquire':
                time.sleep(params['exptime'])

                # fits.PrimaryHDU(fake_data.fake_fli_image()).writeto(params['filepath'])
                shutil.copy(config.FLI.dummy_image_path, params['filepath'])

            return ReturnCode.CAMERA_OK, {}

        else:
            if request_type == 'acquire':
                increment_image_counter()

            url = f'http://{config.FLI.ip}:{config.FLI.port}/{request_type}'
            if params == {}:
                req = requests.get(url, timeout=config.FLI.request_timeout)
            else:
                req = requests.post(url, json=params,
                                    timeout=config.FLI.request_timeout)

            data = json.loads(req.text)

            if req.status_code == 200:
                return ReturnCode.CAMERA_OK, data
            else:
                text = ''

                if data.get('error_text') is not None:
                    text += f' {data.get("error_text")}'

                if data.get('error_status') is not None:
                    text += f' (status = {data.get("error_status")})'

                database.store(
                    'obs', {
                        f'fli_log':
                            f'[ERROR] Camera server answered with an Error {req.status_code}.{text}'
                    })

                return ReturnCode.CAMERA_ERROR, data


def check_server_status():
    """
    Verify if the camera server is up and running and check if the camera can be queried.

    :return: status of the camera server (UP/DOWN/ERROR)
    """

    server_status = services.camera('status')

    if server_status[0] == 'inactive':
        return CameraServerStatus.DOWN

    try:
        r = requests.get(f'http://{config.FLI.ip}:{config.FLI.port}/ping')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return CameraServerStatus.DOWN
    except requests.exceptions.HTTPError:
        return CameraServerStatus.ERROR
    else:
        return CameraServerStatus.UP
