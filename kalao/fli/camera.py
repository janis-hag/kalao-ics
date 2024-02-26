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
import dataclasses
import json
import shutil
import time
from pathlib import Path
from typing import Any

import numpy as np

from kalao import database, logger
from kalao.sequencer.seq_context import with_sequencer_status
from kalao.timers import database as database_timer
from kalao.utils import file_handling

import requests
import requests.exceptions

from kalao.definitions.dataclasses import ROI
from kalao.definitions.enums import (CameraServerStatus, ObservationType,
                                     ReturnCode, SequencerStatus)

import config


def take_empty(filepath: str | Path | None = None) -> Path | None:
    if filepath is None:
        filepath = Path('/tmp/fli_empty.fits')
    elif not isinstance(filepath, Path):
        filepath = Path(filepath)

    params = {'filepath': filepath}
    ret, _ = _send_request('/empty', params)

    if ret == ReturnCode.CAMERA_OK:
        return filepath
    else:
        return None


def take_frame(exptime: float | None = None,
               filepath: str | Path | None = None,
               nbflushes: int | None = None, nbframes: int | None = None,
               roi: ROI | None = None) -> Path | None:
    if filepath is None:
        filepath = Path('/tmp/fli_frame.fits')
    elif not isinstance(filepath, Path):
        filepath = Path(filepath)

    if nbframes == 1:
        nbframes = None

    if roi is None:
        roi_dict = None
    else:
        roi_dict = dataclasses.asdict(roi)

    params = {
        'exptime': exptime,
        'nbframes': nbframes,
        'filepath': filepath,
        'nbflushes': nbflushes,
        'roi': roi_dict
    }

    symlink = config.FITS.last_image_all
    symlink.unlink(missing_ok=True)
    symlink.symlink_to(filepath)

    ret, _ = _send_request('/acquire', params)

    if ret == ReturnCode.CAMERA_OK:
        return filepath
    else:
        return None


@with_sequencer_status(SequencerStatus.EXP)
def take_image(obs_type: ObservationType, exptime: float | None = None,
               filepath: str | Path | None = None, nbframes: int | None = None,
               roi_size: int | None = None,
               comment: str | None = None) -> Path | None:
    """
    :param sequencer_arguments:
    :param exptime: Detector integration time to use
    :param filepath: Path where the file should be stored
    :return: path to the image
    """

    if exptime is not None and exptime < 0.001:
        logger.error(
            'fli',
            f'Abort before exposure started. exptime = {exptime} s is below minimum value of 0.001 s'
        )
        return None
    elif exptime is not None and exptime > config.FLI.request_timeout:
        logger.error(
            'fli',
            f'Abort before exposure started. exptime = {exptime} s is above maximum value of {config.FLI.request_timeout} s'
        )
        return None

    if roi_size is None or roi_size == 1024:
        roi = None
    else:
        roi = ROI(config.FLI.center_x - roi_size//2,
                  config.FLI.center_y - roi_size//2, roi_size, roi_size)

    if filepath is None:
        # Generate filename including path
        filepath = file_handling.get_tmp_image_filepath()

    # Store monitoring status at start of exposure
    database_timer.update_monitoring_db()

    filepath = take_frame(exptime=exptime, filepath=filepath,
                          nbframes=nbframes, roi=roi)

    if filepath is not None:
        database.store('obs', {'fli_temporary_image_path': filepath})
        final_filepath = file_handling.save_tmp_image(filepath, obs_type,
                                                      comment=comment)

        return final_filepath
    else:
        return None


def increment_image_counter(params: dict[str, Any]) -> int:
    """
    Increments the image counter by one

    :return: new image counter value
    """

    try:
        image_count = database.get('obs', 'fli_image_count',
                                   days=3650)['fli_image_count'][0]['value']
    except (KeyError, IndexError):
        image_count = 1

    image_count += 1

    data = {'fli_image_count': image_count}

    if 'exptime' in params:
        data['fli_exposure_time'] = params['exptime']

    database.store('obs', data)

    return image_count


def cancel() -> ReturnCode:
    ret, _ = _send_request('/cancelExposure')

    return ret


def get_exposure_status() -> dict[str, float]:
    ret, exposure_status = _send_request('/exposureStatus')

    if ret == ReturnCode.CAMERA_OK:
        return exposure_status
    else:
        return {
            'remaining_time': -1,
            'exposure_time': -1,
            'frames': -1,
            'remaining_frames': -1
        }


def get_temperatures() -> dict[str, float]:
    """
    Gets CCD and heatsink temperatures from the camera.

    :return:
    """

    ret, temperatures = _send_request('/temperature')

    if ret == ReturnCode.CAMERA_OK:
        return temperatures
    else:
        return {'heatsink': np.inf, 'ccd': np.inf}


def set_temperature(temperature: float) -> ReturnCode:
    """
    Sets the CCD temperature.

    :param temperature:
    :return:
    """
    params = {'temperature': temperature}
    ret, _ = _send_request('/temperature', params)
    return ret


def _send_request(endpoint: str,
                  params: dict[str, Any] = {}) -> tuple[ReturnCode, Any]:
    # Clean params
    for key, value in list(params.items()):
        if value is None:
            del params[key]
        elif key == 'filepath':
            params[key] = str(value)

    if config.FLI.dummy_camera:
        if endpoint == '/acquire':
            time.sleep(params['exptime'])

            # fits.PrimaryHDU(fake_data.fake_fli_image()).writeto(params['filepath'])
            shutil.copy(config.FLI.dummy_image_path, params['filepath'])

        return ReturnCode.CAMERA_OK, {}

    else:
        if endpoint == '/acquire':
            increment_image_counter(params)

        url = f'http://{config.FLI.ip}:{config.FLI.port}{endpoint}'

        try:
            if params == {}:
                req = requests.get(url, timeout=config.FLI.request_timeout)
            else:
                req = requests.post(url, json=params,
                                    timeout=config.FLI.request_timeout)
        except requests.exceptions.RequestException:
            logger.error(
                'fli',
                f'Camera server endpoint {endpoint} answered with a error.')
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
                f'Camera server endpoint {endpoint} answered with an Error {req.status_code}.{text}'
            )

            return ReturnCode.CAMERA_ERROR, data


def check_server_status() -> CameraServerStatus:
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
