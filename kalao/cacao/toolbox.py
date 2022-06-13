#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import numpy as np
from astropy.nddata.blocks import block_reduce

import subprocess
from subprocess import PIPE, STDOUT
from CacaoProcessTools import fps, FPS_status

def get_roi_and_subapertures(data):
    roi = None
    subapertures = None

    if data.shape == (128, 128):
        roi = data[9:119, 9:119]
        subapertures = np.empty((121, 10, 10), int)
        for i in range(11):
            for j in range(11):
                subapertures[j + 11 * i] = roi[i * 10:10 + i * 10, j * 10:10 + j * 10]

    elif data.shape == (64, 64):
        roi = data[4:60, 4:60]
        subapertures = np.empty((121, 4, 4), int)
        for i in range(11):
            for j in range(11):
                subapertures[j + 11 * i] = roi[1 + i * 5:5 + i * 5, 1 + j * 5:5 + j * 5]

    return roi, subapertures


def get_actuator_2d(i):
    if i is None or i < 0 or i >= 140:
        return (None, None)
    elif i < 10:
        return ((i + 1) // 12, (i + 1) % 12)
    elif i < 130:
        return ((i + 2) // 12, (i + 2) % 12)
    elif i < 140:
        return ((i + 3) // 12, (i + 3) % 12)


def get_actuator_1d(x, y):
    if x is None or y is None or \
            x < 0 or x >= 12 or \
            y < 0 or y >= 12 or \
            x == 0 and y == 0 or \
            x == 0 and y == 11 or \
            x == 11 and y == 0 or \
            x == 11 and y == 11:
        return None
    if x < 1:
        return x * 12 + y - 1
    elif x < 11:
        return x * 12 + y - 2
    elif x < 12:
        return x * 12 + y - 3


def get_subaperture_2d(i):
    if i is None or i < 0 or i >= 121:
        return (None, None)
    else:
        return (i // 11, i % 11)


def get_subaperture_1d(x, y):
    if x is None or y is None or \
            x < 0 or x >= 11 or \
            y < 0 or y >= 11:
        return None
    else:
        return x * 11 + y


def get_subapertures_around_actuator(i):
    if i is None:
        return (None, None, None, None)

    x, y = get_actuator_2d(i)

    return (get_subaperture_1d(x - 1, y - 1),
            get_subaperture_1d(x - 1, y),
            get_subaperture_1d(x, y - 1),
            get_subaperture_1d(x, y))


def get_wfs_flux_map(upsampling=4):
    size = 56 * upsampling

    radius_out = 25 * upsampling
    radius_in = radius_out * 336.4 / 1200

    xx, yy = np.mgrid[:size, :size]
    circle = (xx - size / 2 + 0.5) ** 2 + (yy - size / 2 + 0.5) ** 2
    pupil = np.logical_and(circle <= radius_out ** 2, circle >= radius_in ** 2)
    pupil = block_reduce(pupil, upsampling)
    pupil = pupil / upsampling ** 2

    side_real = 5
    side = side_real * upsampling
    offset = 3 * upsampling

    xx, yy = np.mgrid[:size, :size]
    xx = np.abs(xx - offset + 0.5)
    yy = np.abs(yy - offset + 0.5)
    subap = np.logical_and(xx <= side / 2, yy <= side / 2)
    subap = block_reduce(subap, upsampling)
    subap = subap / upsampling ** 2

    flux = np.zeros((11, 11))

    for i in range(11):
        for j in range(11):
            subap_tmp = np.roll(subap, (i * side_real, j * side_real), (0, 1))

            flux[i, j] = np.sum(subap_tmp * pupil) / (side_real) ** 2

    return flux


def save_stream_to_fits(stream_name, fits_file):
    milk_input = f"""
    readshmim "{stream_name}"
    saveFITS "{stream_name}" "{fits_file}"
    exitCLI
    """

    cp = subprocess.run(["/usr/local/milk/bin/milk"], input=milk_input, encoding='utf8', stdout=PIPE, stderr=STDOUT)

    return cp


def wfs_centering(tt_threshold):

    tip_centered = False
    tilt_centered = False

    fps_slopes = fps("shwfs_process")
    fps_bmc = fps("bmc_display")

    #TODO add iterations limit to prevent infinite loop
    while not (tip_centered and tilt_centered):

        tilt = fps_slopes.get_param_value_float('slope_x')
        tip = fps_slopes.get_param_value_float('slope_y')

        tip_offset = fps_bmc.get_param_value_float("ttm_tip_offset")
        tilt_offset = fps_bmc.get_param_value_float("ttm_tilt_offset")

        if tip_offset - tip < tt_threshold:
            tip_centered = True
        else:
            fps_bmc.set_param_value_float('ttm_tip_offset', str(tip_offset - tip / 2))

        if tilt_offset - tip < tt_threshold:
            tilt_centered = True
        else:
            fps_bmc.set_param_value_float('ttm_tilt_offset', str(tilt_offset - tilt / 2))

    # TODO return 0 if centered, 1 if exceeded iterations
    return 0

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    plt.imshow(get_wfs_flux_map())
    plt.colorbar()
    plt.show()
