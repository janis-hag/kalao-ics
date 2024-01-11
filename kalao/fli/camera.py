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


def take_frame(dit, filepath=None, nbflushes=None):
    if filepath is None:
        filepath = '/tmp/fli_frame.fits'

    params = {'exptime': dit, 'filepath': filepath, 'nbflushes': nbflushes}
    ret, _ = _send_request('acquire', params)

    if ret == ReturnCode.CAMERA_OK:
        img = fits.getdata(filepath)

        _update_fli_stream(img, filepath)

        return img
    else:
        return None


def take_cube(dit, nbframes, filepath=None, nbflushes=None):
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

        _update_fli_stream(img_cube[-1], filepath)

        return img_cube
    else:
        return None


def _update_fli_stream(img, filepath):
    filepath = Path(filepath)

    if fli_stream.shape == img.shape:
        fli_stream.set_data(img, True)

        keywords = {
            'laser': flipmirror.get_position() == FlipMirrorPosition.UP,
        }

        for i in range(math.ceil(len(filepath.name) / 16)):
            keywords[f'filepath_{i}'] = str(filepath.name)[i * 16:(i+1) * 16]

        fli_stream.set_keywords(keywords)
    else:
        logger.error(
            'fli',
            f'{config.Streams.FLI} not updated, shapes are inconsistent (stream={fli_stream.shape}, frame={img.shape}).'
        )


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
        logger.error(
            'fli',
            f'Abort before exposure started. DIT={dit} below min value 0.001')
        return None

    if filepath is None:
        # Generate filename including path
        filepath = file_handling.generate_image_filepath()

    # Store monitoring status at start of exposure
    database_timer.update_monitoring_db()

    database.store('obs', {
        'sequencer_status': SequencerStatus.EXP,
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


def increment_image_counter(exptime):
    """
    Increments the image counter by one

    :return: new image counter value
    """

    image_count = database.get_last_value('obs', 'fli_image_count')

    if image_count is None:
        image_count = 1
    else:
        image_count += 1

    database.store('obs', {
        'fli_image_count': image_count,
        'fli_exposure_time': exptime
    })

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
        return {'remaining_time': -1, 'exposure_time': -1, 'frames': -1, 'remaining_frames': -1}


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
            increment_image_counter(params['exptime'])

        url = f'http://{config.FLI.ip}:{config.FLI.port}/{request_type}'

        try:
            if params == {}:
                req = requests.get(url, timeout=config.FLI.request_timeout)
            else:
                req = requests.post(url, json=params,
                                    timeout=config.FLI.request_timeout)
        except requests.exceptions.ConnectionError:
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
