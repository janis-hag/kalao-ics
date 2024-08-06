#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import numpy as np

from astropy.io import fits

import libtmux
import libtmux.exc

from kalao import logger

from kalao.definitions.enums import ReturnCode

try:
    from pyMilk.interfacing.fps import FPS
    from pyMilk.interfacing.shm import SHM
except ImportError:

    class SHM:
        def __init__(self, name, data=None, location=None, shared=None):
            self.nptype = None
            self.shape = None
            self.IMAGE = None

        def get_data(self, check=False):
            pass

        def set_data(self, data, check_type=False):
            pass

        def get_keywords(self):
            pass

        def close(self):
            pass

    class FPS:
        def __init__(self, name):
            pass

        def get_param(self, name):
            pass

        def set_param(self, name, value):
            pass

        def conf_isrunning(self):
            pass

        def run_isrunning(self):
            pass

        def disconnect(self):
            pass


@dataclass
class SHMInfo:
    shm: SHM
    stat: os.stat_result


@dataclass
class FPSInfo:
    fps: FPS
    stat: os.stat_result


milk_path = Path('/tmp/milk')

# Will be shared within a process
shm_cache: dict[str, SHMInfo] = {}
fps_cache: dict[str, FPSInfo] = {}


def open_or_create_shm(shm_name: str, shape: tuple[int, ...],
                       dtype: type) -> SHM:
    shm_path = milk_path / (shm_name+'.im.shm')

    if shm_path.exists():
        shm = get_shm(shm_name)
    else:
        img = np.zeros(shape, dtype)

        shm = SHM(
            shm_name,
            img,
            location=-1,  # CPU
            shared=True,  # Shared
        )

    return shm


def get_shm(shm_name: str) -> SHM | None:
    shm_info = shm_cache.get(shm_name)
    shm_path = milk_path / (shm_name+'.im.shm')

    if not shm_path.exists():
        return None

    stat = shm_path.stat()

    if shm_info is not None and stat.st_ino == shm_info.stat.st_ino and math.isclose(
            stat.st_ctime, shm_info.stat.st_ctime):
        return shm_info.shm
    else:
        if shm_info is not None:
            shm_info.shm.close()

        shm = SHM(shm_name)
        shm_cache[shm_name] = SHMInfo(shm, stat)
        return shm


def get_fps(fps_name: str) -> FPS | None:
    fps_info = fps_cache.get(fps_name)
    fps_path = milk_path / (fps_name+'.fps.shm')

    if not fps_path.exists():
        return None

    stat = fps_path.stat()

    # Note: only check inode number as ctime is too aggressive
    if fps_info is not None and stat.st_ino == fps_info.stat.st_ino:
        return fps_info.fps
    else:
        if fps_info is not None:
            fps_info.fps.disconnect()

        fps = FPS(fps_name)
        fps_cache[fps_name] = FPSInfo(fps, stat)
        return fps


def zero_stream(stream_or_name: str | SHM | None) -> ReturnCode:
    if stream_or_name is None:
        return ReturnCode.OK
    elif isinstance(stream_or_name, SHM):
        stream_shm = stream_or_name
    else:
        stream_shm = get_shm(stream_or_name)

        if stream_shm is None:
            return ReturnCode.GENERIC_ERROR

    pattern = np.zeros(stream_shm.shape, stream_shm.nptype)
    stream_shm.set_data(pattern)

    return ReturnCode.OK


def save_stream_to_fits(stream_or_name: str | SHM | None,
                        fits_file: str | Path) -> ReturnCode:
    if stream_or_name is None:
        return ReturnCode.OK
    elif isinstance(stream_or_name, SHM):
        stream_shm = stream_or_name
    else:
        stream_shm = get_shm(stream_or_name)

        if stream_shm is None:
            return ReturnCode.GENERIC_ERROR

    fits.PrimaryHDU(stream_shm.get_data(check=True)).writeto(fits_file)

    return ReturnCode.OK


def load_fits_to_stream(fits_file: str | Path,
                        stream_or_name: str | SHM) -> ReturnCode:
    if stream_or_name is None:
        return ReturnCode.GENERIC_ERROR
    elif isinstance(stream_or_name, SHM):
        stream_shm = stream_or_name
    else:
        stream_shm = get_shm(stream_or_name)

        if stream_shm is None:
            return ReturnCode.GENERIC_ERROR

    pattern = fits.getdata(fits_file)

    if pattern.shape != stream_shm.shape:
        return ReturnCode.GENERIC_ERROR

    stream_shm.set_data(pattern, True)

    return ReturnCode.OK


ReturnValue = TypeVar('ReturnValue', int, float, str, bool)


def set_fps_value(fps_name: str, key: str,
                  value: ReturnValue) -> ReturnValue | None:
    fps = get_fps(fps_name)

    if fps is None:
        logger.error('ao', f'Can\'t set {key}, {fps_name} is missing')
        return None

    fps.set_param(key, value)

    return fps.get_param(key)


def set_tmux_value(session_name: str, key: str,
                   value: ReturnValue | None = None) -> ReturnValue | None:
    server = libtmux.Server()

    try:
        session = server.sessions.get(session_name=session_name)
        pane = session.attached_pane

        if value is None:
            pane.send_keys(f'{key}()', enter=True)
        else:
            pane.send_keys(f'{key}({value})', enter=True)

        time.sleep(1)

        stdout = pane.cmd('capture-pane', '-p').stdout

        return_str = ''
        i = -2

        while -i <= len(stdout) and not stdout[i].startswith('>>>'):
            return_str = stdout[i] + '\n' + return_str
            i -= 1

        if return_str == '':
            return None
        else:
            return eval(return_str)

    except (libtmux.exc.TmuxObjectDoesNotExist,
            libtmux._internal.query_list.ObjectDoesNotExist):
        logger.error('ao', f'Can\'t set {key}, {session_name} is missing')
        return None


def wait_file(file: str | Path, timeout: float = 30,
              wait_time: float = 1) -> ReturnCode:
    if not isinstance(file, Path):
        file = Path(file)

    start = time.monotonic()

    while True:
        if file.exists():
            return ReturnCode.OK
        elif (time.monotonic() - start) > timeout:
            return ReturnCode.TIMEOUT

        time.sleep(wait_time)
