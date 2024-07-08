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
from pathlib import Path
from typing import Any

import numpy as np

from kalao import database, logger
from kalao.sequencer.seq_context import with_sequencer_status
from kalao.utils import file_handling

import requests
import requests.exceptions

from kalao.definitions.dataclasses import ROI
from kalao.definitions.enums import (CameraServerStatus, CameraStatus,
                                     ObservationType, ReturnCode,
                                     SequencerStatus)

import config


def take_fake(filepath: str | Path | None = None,
              nbframes: int | None = None) -> Path | None:
    if filepath is None:
        filepath = Path('/tmp/camera_fake.fits')
    elif not isinstance(filepath, Path):
        filepath = Path(filepath)

    if nbframes == 1:
        nbframes = None

    params = {
        'filepath': filepath,
        'nbframes': nbframes,
    }
    ret, _ = _send_request('/fake', params)

    if ret == ReturnCode.CAMERA_OK:
        return filepath
    else:
        return None


def take_frame(filepath: str | Path | None = None,
               exptime: float | None = None, nbframes: int | None = None,
               roi: ROI | None = None,
               nbflushes: int | None = None) -> Path | None:
    if filepath is None:
        filepath = Path('/tmp/camera_frame.fits')
    elif not isinstance(filepath, Path):
        filepath = Path(filepath)

    if nbframes == 1:
        nbframes = None

    if roi is None:
        roi_dict = None
    else:
        roi_dict = dataclasses.asdict(roi)

    params = {
        'filepath': filepath,
        'exptime': exptime,
        'nbframes': nbframes,
        'roi': roi_dict,
        'nbflushes': nbflushes,
    }

    symlink = config.FITS.last_image_all
    symlink.unlink(missing_ok=True)
    symlink.symlink_to(filepath)

    ret, _ = _send_request('/acquire', params)

    if ret == ReturnCode.CAMERA_OK:
        if filepath.exists():
            return filepath
        else:
            return None
    else:
        return None


@with_sequencer_status(SequencerStatus.EXP)
def take_image(obs_type: ObservationType, exptime: float | None = None,
               filepath: str | Path | None = None, nbframes: int | None = None,
               roi_size: int | None = None,
               comment: str | None = None) -> Path | None:

    if exptime is not None and exptime < 0.001:
        logger.error(
            'camera',
            f'Abort before exposure started. exptime = {exptime} s is below minimum value of 0.001 s'
        )
        return None
    elif exptime is not None and exptime > config.Camera.request_timeout:
        logger.error(
            'camera',
            f'Abort before exposure started. exptime = {exptime} s is above maximum value of {config.Camera.request_timeout} s'
        )
        return None

    if roi_size is None or roi_size == 1024:
        roi = None
    else:
        roi = ROI(config.Camera.center_x - roi_size//2,
                  config.Camera.center_y - roi_size//2, roi_size, roi_size)

    if filepath is None:
        # Generate filename including path
        filepath = file_handling.get_tmp_image_filepath()

    filepath = take_frame(filepath=filepath, exptime=exptime,
                          nbframes=nbframes, roi=roi)

    if filepath is not None:
        database.store('obs', {'camera_temporary_image_path': filepath})
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

    image_count = database.get_last_value('obs', 'camera_image_count')

    if image_count is None:
        image_count = 0
    else:
        image_count += 1

    data = {'camera_image_count': image_count}

    if 'exptime' in params:
        data['camera_exposure_time'] = params['exptime']

    database.store('obs', data)

    return image_count


def cancel(keepframe: bool | None = None) -> ReturnCode:
    params = {
        'keepframe': keepframe,
    }

    ret, _ = _send_request('/cancelExposure', params)

    return ret


def get_camera_status() -> str:
    ret, camera_status = _send_request('/cameraStatus')

    if ret == ReturnCode.CAMERA_OK:
        return camera_status['status']
    else:
        return CameraStatus.ERROR


def get_exposure_status() -> dict[str, float]:
    ret, exposure_status = _send_request('/exposureStatus')

    if ret == ReturnCode.CAMERA_OK:
        return exposure_status
    else:
        return {
            'remaining_time': np.nan,
            'exposure_time': np.nan,
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
        return {'heatsink': np.nan, 'ccd': np.nan}


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

    if endpoint == '/acquire':
        increment_image_counter(params)

    url = f'http://{config.Camera.ip}:{config.Camera.port}{endpoint}'

    try:
        if params == {}:
            req = requests.get(url, timeout=config.Camera.request_timeout)
        else:
            req = requests.post(url, json=params,
                                timeout=config.Camera.request_timeout)
    except requests.exceptions.RequestException as e:
        logger.error(
            'camera',
            f'Camera server endpoint {endpoint} answered with a {e.__class__.__name__} exception.'
        )
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
            'camera',
            f'Camera server endpoint {endpoint} answered with an Error {req.status_code}.{text}'
        )

        return ReturnCode.CAMERA_ERROR, data


def server_status() -> CameraServerStatus:
    """
    Verify if the camera server is up and running and check if the camera can be queried.

    :return: status of the camera server (UP/DOWN/ERROR)
    """
    try:
        r = requests.get(
            f'http://{config.Camera.ip}:{config.Camera.port}/ping')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return CameraServerStatus.DOWN
    except Exception:
        return CameraServerStatus.ERROR
    else:
        return CameraServerStatus.UP
