#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

from pathlib import Path

import numpy as np

from astropy.io import fits

from pyMilk.interfacing import isio_shmlib
from pyMilk.interfacing.fps import FPS
from pyMilk.interfacing.shm import SHM


def check_stream(stream_name):
    """
    Function verifies if stream_name exists

    :param stream_name: stream to check existence
    :return: boolean, stream_name_clean
    """
    # stream_path = Path(os.environ["MILK_SHM_DIR"])
    milk_path = Path('/tmp/milk')
    stream_name_clean = isio_shmlib.check_SHM_name(stream_name)
    stream_path = milk_path / (stream_name_clean+'.im.shm')

    return stream_path.exists(), stream_name_clean


def check_fps(fps_name):
    """
    Function verifies if fps_name exists

    :param fps_name: fps to check existence
    :return: boolean, fps_name_clean
    """
    # fps_path = Path(os.environ["MILK_SHM_DIR"])
    milk_path = Path('/tmp/milk')
    fps_name_clean = isio_shmlib.check_SHM_name(fps_name)
    fps_path = milk_path / (fps_name_clean+'.fps.shm')

    return fps_path.exists(), fps_name_clean


def open_or_create_stream(stream_name, shape, dtype):
    stream_exists, stream_name = check_stream(stream_name)

    if stream_exists:
        shm = SHM(stream_name)
    else:
        img = np.zeros(shape, dtype)

        shm = SHM(
            stream_name,
            img,
            location=-1,  # CPU
            shared=True,  # Shared
        )

    return shm


def open_stream_once(stream_name, streams_list={}):
    opened_stream = streams_list.get(stream_name)

    if opened_stream is None:
        stream_exists, stream_name = check_stream(stream_name)

        if stream_exists:
            opened_stream = SHM(stream_name)
            streams_list[stream_name] = opened_stream
            return opened_stream
        else:
            return None
    else:
        return opened_stream


def open_fps_once(fps_name, fps_list):
    opened_fps = fps_list.get(fps_name)

    if opened_fps is None:
        fps_exists, fps_name = check_fps(fps_name)

        if fps_exists:
            opened_fps = FPS(fps_name)
            fps_list[fps_name] = opened_fps
            return opened_fps
        else:
            return None
    else:
        return opened_fps


def zero_stream(stream_or_name):
    if stream_or_name is None:
        return -1
    elif isinstance(stream_or_name, SHM):
        stream_shm = stream_or_name
    else:
        stream_exists, stream_name = check_stream(stream_or_name)

        if not stream_exists:
            return -1

        stream_shm = SHM(stream_name)

    pattern = np.zeros(stream_shm.shape, stream_shm.nptype)
    stream_shm.set_data(pattern)

    return 0


def save_stream_to_fits(stream_or_name, fits_file):
    if stream_or_name is None:
        return -1
    elif isinstance(stream_or_name, SHM):
        stream_shm = stream_or_name
    else:
        stream_exists, stream_name = check_stream(stream_or_name)

        if not stream_exists:
            return -1

        stream_shm = SHM(stream_name)

    fits.PrimaryHDU(stream_shm.get_data(True)).writeto(fits_file)

    return 0


def load_fits_to_stream(fits_file, stream_or_name):
    if stream_or_name is None:
        return -1
    elif isinstance(stream_or_name, SHM):
        stream_shm = stream_or_name
    else:
        stream_exists, stream_name = check_stream(stream_or_name)

        if not stream_exists:
            return -1

        stream_shm = SHM(stream_name)

    pattern = fits.getdata(fits_file)

    if pattern.shape != stream_shm.shape:
        return -1

    stream_shm.set_data(pattern, True)

    return 0
