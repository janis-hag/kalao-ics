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
from pathlib import Path
from typing import Any

import numpy as np

import requests
import requests.exceptions

from kalao import logger
from kalao.utils import fits_handling

from kalao.definitions.dataclasses import ROI, Template
from kalao.definitions.enums import (CameraServerStatus, CameraStatus,
                                     ReturnCode, TemplateID)

import config


def get_test_image(filepath: str | Path = None, exptime: float | None = None,
                   nbframes: int | None = None) -> Path | None:
    if filepath is None:
        filepath = Path('/tmp/camera_test.fits')
    elif not isinstance(filepath, Path):
        filepath = Path(filepath)

    if nbframes == 1:
        nbframes = None

    params = {
        'filepath': filepath,
        'exptime': exptime,
        'nbframes': nbframes,
    }

    ret, _ = _send_request('POST', '/testImage', params)

    if ret == ReturnCode.CAMERA_OK:
        return filepath
    else:
        return None


def take_image(filepath: str | Path | None = None,
               exptime: float | None = None, nbframes: int | None = None,
               roi: ROI | None = None,
               nbflushes: int | None = None) -> Path | None:
    if filepath is None:
        filepath = Path('/tmp/camera_image.fits')
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

    ret, _ = _send_request('POST', '/acquire', params)

    if ret == ReturnCode.CAMERA_OK:
        return filepath
    else:
        return None


def take_science_image(template: Template, exptime: float | None = None,
                       filepath: str | Path | None = None, nbframes: int |
                       None = None, roi_size: int | None = None,
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
        roi = ROI(x=config.Camera.center_x - roi_size//2,
                  y=config.Camera.center_y - roi_size//2, width=roi_size,
                  height=roi_size)

    if filepath is None:
        # Generate filename including path
        filepath = fits_handling.get_tmp_image_filepath()

    template.next_exposure()

    if template.id == TemplateID.SELF_TEST:
        filepath = get_test_image(filepath=filepath, exptime=exptime,
                                  nbframes=nbframes)
    else:
        filepath = take_image(filepath=filepath, exptime=exptime,
                              nbframes=nbframes, roi=roi)

    if filepath is not None:
        final_filepath = fits_handling.save_image(filepath, template,
                                                  comment=comment)

        return final_filepath
    else:
        return None


def cancel(keepframe: bool | None = None) -> ReturnCode:
    params = {
        'keepframe': keepframe,
    }

    ret, _ = _send_request('POST', '/cancelExposure', params)

    return ret


def get_camera_status() -> str:
    ret, camera_status = _send_request('GET', '/cameraStatus')

    if ret == ReturnCode.CAMERA_OK:
        return camera_status['status']
    elif ret == ReturnCode.CAMERA_SERVER_UNREACHABLE:
        return CameraStatus.SERVER_UNREACHABLE
    else:
        return CameraStatus.ERROR


def get_exposure_status() -> dict[str, float]:
    ret, exposure_status = _send_request('GET', '/exposureStatus')

    if ret == ReturnCode.CAMERA_OK:
        return exposure_status
    else:
        return {
            'remaining_time': np.nan,
            'exposure_time': np.nan,
            'frames': -1,
            'remaining_frames': -1
        }


def set_exposure_time(exptime) -> ReturnCode:
    params = {'exptime': exptime}
    ret, _ = _send_request('POST', '/exposureTime', params)
    return ret


def get_temperatures() -> dict[str, float]:
    """
    Gets CCD and heatsink temperatures from the camera.

    :return:
    """

    ret, temperatures = _send_request('GET', '/temperatures')

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
    ret, _ = _send_request('POST', '/temperature', params)
    return ret


def _send_request(method: str, endpoint: str, params: dict[str, Any] |
                  None = None) -> tuple[ReturnCode, Any]:
    if params is not None:
        # Clean params
        for key, value in list(params.items()):
            if value is None:
                del params[key]
            elif key == 'filepath':
                params[key] = str(value)

    kwargs = {}
    if method == 'POST' and params is not None:
        kwargs['json'] = params

    try:
        req = requests.request(
            method,
            f'http://{config.Camera.host}:{config.Camera.port}{endpoint}',
            timeout=config.Camera.request_timeout, **kwargs)

        req.raise_for_status()

        if req.headers.get('content-type', '').startswith('application/json'):
            return ReturnCode.CAMERA_OK, req.json()
        else:
            return ReturnCode.CAMERA_OK, req.text

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return ReturnCode.CAMERA_SERVER_UNREACHABLE, None

    except requests.exceptions.HTTPError:
        logger.error(
            'camera',
            f'Camera server endpoint {endpoint} answered with an Error {req.status_code}, {req.text}'
        )
        return ReturnCode.CAMERA_ERROR, None


def server_status() -> CameraServerStatus:
    """
    Verify if the camera server is up and running and check if the camera can be queried.

    :return: status of the camera server (UP/DOWN/ERROR)
    """
    try:
        r = requests.get(
            f'http://{config.Camera.host}:{config.Camera.port}/ping')
        r.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return CameraServerStatus.DOWN
    except requests.exceptions.HTTPError:
        return CameraServerStatus.ERROR
    else:
        return CameraServerStatus.UP
