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
import math
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from astropy.io import fits

from kalao import database, logger
from kalao.cacao import toolbox
from kalao.plc import flipmirror
from kalao.timers import database as database_timer
from kalao.utils import file_handling

import requests
import requests.exceptions

from kalao.definitions.enums import (CameraServerStatus, FlipMirrorPosition,
                                     ReturnCode, SequencerStatus)

import config

fli_stream = toolbox.open_or_create_stream(config.Streams.FLI, (1024, 1024),
                                           np.uint16)


def take_empty(filepath=None):
    if filepath is None:
        filepath = '/tmp/fli_empty.fits'

    params = {'filepath': filepath}
    ret, _ = _send_request('empty', params)

    return ret


def take_frame(exptime=None, filepath=None, nbflushes=None, roi=None,
               nbframes=None):
    if filepath is None:
        filepath = '/tmp/fli_frame.fits'

    if nbframes == 1:
        nbframes = None

    if roi is not None:
        roi = {'x': roi[0], 'y': roi[1], 'width': roi[2], 'height': roi[3]}

    params = {
        'exptime': exptime,
        'nbframes': nbframes,
        'filepath': filepath,
        'nbflushes': nbflushes,
        'roi': roi
    }

    ret, _ = _send_request('acquire', params)

    if ret == ReturnCode.CAMERA_OK:
        img = fits.getdata(filepath)

        _update_fli_stream(img, filepath)

        return img
    else:
        return None


def _update_fli_stream(img, filepath):
    filepath = Path(filepath)

    if len(img.shape) == 3:
        img = img[-1]

    if fli_stream.shape == img.shape:
        fli_stream.set_data(img, True)

        keywords = {
            'laser': flipmirror.get_position() == FlipMirrorPosition.UP,
            'timestamp': datetime.now(timezone.utc).timestamp(),
        }

        for i in range(math.ceil(len(filepath.name) / 16)):
            keywords[f'filepath_{i}'] = str(filepath.name)[i * 16:(i+1) * 16]

        fli_stream.set_keywords(keywords)
    # else:
    #     logger.error(
    #         'fli',
    #         f'{config.Streams.FLI} not updated, shapes are inconsistent (stream = {fli_stream.shape}, frame = {img.shape}).'
    #     )


def take_image(obs_type, exptime=None, filepath=None):
    """
    :param sequencer_arguments:
    :param exptime: Detector integration time to use
    :param filepath: Path where the file should be stored
    :return: path to the image
    """

    if exptime is not None and exptime < 0.001:
        logger.error(
            'fli',
            f'Abort before exposure started. exptime = {exptime} s below minimum value of 0.001 s'
        )
        return None

    if filepath is None:
        # Generate filename including path
        filepath = file_handling.get_tmp_image_filepath()

    # Store monitoring status at start of exposure
    database_timer.update_monitoring_db()

    database.store('obs', {
        'sequencer_status': SequencerStatus.EXP,
    })

    img = take_frame(exptime=exptime, filepath=filepath)

    if img is not None:
        database.store('obs', {'fli_temporary_image_path': filepath})
        target_path_name = file_handling.save_tmp_image(filepath, obs_type)

        return target_path_name
    else:
        return None


def increment_image_counter(params):
    """
    Increments the image counter by one

    :return: new image counter value
    """

    image_count = database.get_last_value('obs', 'fli_image_count')

    if image_count is None:
        image_count = 1
    else:
        image_count += 1

    data = {'fli_image_count': image_count}

    if 'exptime' in params:
        data['fli_exposure_time'] = params['exptime']

    database.store('obs', data)

    return image_count


def cancel():
    # TODO add docstring

    ret, _ = _send_request('cancelExposure')

    return ret


def get_exposure_status():
    ret, exposure_status = _send_request('exposureStatus')

    if ret == ReturnCode.CAMERA_OK:
        return exposure_status
    else:
        return {
            'remaining_time': -1,
            'exposure_time': -1,
            'frames': -1,
            'remaining_frames': -1
        }


def get_temperatures():
    """
    Gets CCD and heatsink temperatures from the camera.

    :return:
    """

    ret, temperatures = _send_request('temperature')

    if ret == ReturnCode.CAMERA_OK:
        return temperatures
    else:
        return {'heatsink': np.inf, 'ccd': np.inf}


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
        elif key == 'filepath':
            params[key] = str(value)

    if config.FLI.dummy_camera:
        if request_type == 'acquire':
            time.sleep(params['exptime'])

            # fits.PrimaryHDU(fake_data.fake_fli_image()).writeto(params['filepath'])
            shutil.copy(config.FLI.dummy_image_path, params['filepath'])

        return ReturnCode.CAMERA_OK, {}

    else:
        if request_type == 'acquire':
            increment_image_counter(params)

        url = f'http://{config.FLI.ip}:{config.FLI.port}/{request_type}'

        try:
            if params == {}:
                req = requests.get(url, timeout=config.FLI.request_timeout)
            else:
                req = requests.post(url, json=params,
                                    timeout=config.FLI.request_timeout)
        except requests.exceptions.RequestException:
            return ReturnCode.CAMERA_SERVER_DOWN, None

        try:
            data = json.loads(req.text)
        except Exception:
            data = req.text

        if req.status_code == 200:
            return ReturnCode.CAMERA_OK, data
        else:
            text = ''

            if isinstance(data, dict):
                if data.get('error_text') is not None:
                    text += f' {data.get("error_text")}'

                if data.get('error_status') is not None:
                    text += f' (status = {data.get("error_status")})'
            else:
                text = f' {data}'

            logger.error(
                'fli',
                f'Camera server answered with an Error {req.status_code}.{text}'
            )

            return ReturnCode.CAMERA_ERROR, data


def check_server_status():
    """
    Verify if the camera server is up and running and check if the camera can be queried.

    :return: status of the camera server (UP/DOWN/ERROR)
    """
    try:
        r = requests.get(f'http://{config.FLI.ip}:{config.FLI.port}/ping')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return CameraServerStatus.DOWN
    except Exception:
        return CameraServerStatus.ERROR
    else:
        return CameraServerStatus.UP
