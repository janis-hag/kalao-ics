#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""
import math
from pathlib import Path

import numpy as np

from astropy.io import fits

from pyMilk.interfacing.fps import FPS
from pyMilk.interfacing.shm import SHM

milk_path = Path('/tmp/milk')

# Will be shared within a process
cache = {}


def open_or_create_stream(stream_name, shape, dtype):
    shm_path = milk_path / (stream_name+'.im.shm')

    if shm_path.exists():
        shm = open_stream_once(stream_name)
    else:
        img = np.zeros(shape, dtype)

        shm = SHM(
            stream_name,
            img,
            location=-1,  # CPU
            shared=True,  # Shared
        )

    return shm


def open_stream_once(stream_name):
    shm_info = cache.get(stream_name)
    shm_path = milk_path / (stream_name+'.im.shm')

    if not shm_path.exists():
        return None

    stat = shm_path.stat()

    if shm_info is not None and stat.st_ino == shm_info[
            'stat'].st_ino and math.isclose(stat.st_ctime,
                                            shm_info['stat'].st_ctime):
        return shm_info['shm']
    else:
        if shm_info is not None:
            shm_info['shm'].close()

        shm = SHM(stream_name)
        cache[stream_name] = {
            'shm': shm,
            'stat': stat,
        }
        return shm


def open_fps_once(fps_name):
    fps_info = cache.get(fps_name)
    fps_path = milk_path / (fps_name+'.fps.shm')

    if not fps_path.exists():
        return None

    stat = fps_path.stat()

    # Note: only check inode number as ctime is too aggressive
    if fps_info is not None and stat.st_ino == fps_info['stat'].st_ino:
        return fps_info['fps']
    else:
        if fps_info is not None:
            fps_info['fps'].disconnect()

        fps = FPS(fps_name)
        cache[fps_name] = {
            'fps': fps,
            'stat': stat,
        }
        return fps


def zero_stream(stream_or_name):
    if stream_or_name is None:
        return -1
    elif isinstance(stream_or_name, SHM):
        stream_shm = stream_or_name
    else:
        stream_shm = open_stream_once(stream_or_name)

        if stream_shm is None:
            return -1

    pattern = np.zeros(stream_shm.shape, stream_shm.nptype)
    stream_shm.set_data(pattern)

    return 0


def save_stream_to_fits(stream_or_name, fits_file):
    if stream_or_name is None:
        return -1
    elif isinstance(stream_or_name, SHM):
        stream_shm = stream_or_name
    else:
        stream_shm = open_stream_once(stream_or_name)

        if stream_shm is None:
            return -1

    fits.PrimaryHDU(stream_shm.get_data(True)).writeto(fits_file)

    return 0


def load_fits_to_stream(fits_file, stream_or_name):
    if stream_or_name is None:
        return -1
    elif isinstance(stream_or_name, SHM):
        stream_shm = stream_or_name
    else:
        stream_shm = open_stream_once(stream_or_name)

        if stream_shm is None:
            return -1

    pattern = fits.getdata(fits_file)

    if pattern.shape != stream_shm.shape:
        return -1

    stream_shm.set_data(pattern, True)

    return 0
