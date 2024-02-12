import numpy as np
import pandas as pd

from astropy.nddata import block_reduce

# The convention is x = row, y = column


def get_roi_and_subapertures(data):
    roi = None
    subapertures = None

    if data.shape == (128, 128):
        roi = data[9:119, 9:119]
        subapertures = np.empty((121, 10, 10), int)
        for i in range(11):
            for j in range(11):
                subapertures[j + 11*i] = roi[i * 10:10 + i*10,
                                             j * 10:10 + j*10]

    elif data.shape == (64, 64):
        roi = data[4:60, 4:60]
        subapertures = np.empty((121, 4, 4), int)
        for i in range(11):
            for j in range(11):
                subapertures[j + 11*i] = roi[1 + i*5:5 + i*5, 1 + j*5:5 + j*5]

    return roi, subapertures


def get_actuator_2d(i):
    if i is None or i < 0 or i >= 140:
        return (None, None)
    elif i < 10:
        return ((i+1) // 12, (i+1) % 12)
    elif i < 130:
        return ((i+2) // 12, (i+2) % 12)
    elif i < 140:
        return ((i+3) // 12, (i+3) % 12)


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
        return x*12 + y - 1
    elif x < 11:
        return x*12 + y - 2
    elif x < 12:
        return x*12 + y - 3


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
        return x*11 + y


def get_subapertures_around_actuator(i):
    if i is None:
        return (None, None, None, None)

    x, y = get_actuator_2d(i)

    return (get_subaperture_1d(x - 1, y - 1), get_subaperture_1d(x - 1, y),
            get_subaperture_1d(x, y - 1), get_subaperture_1d(x, y))


def subaperture_to_slopes_2d(i):
    row = i // 11
    col = i % 11

    return [(row, col), (row, col + 11)]


def read_spots_file(file):
    spots_df = pd.read_csv(file, delim_whitespace=True, header=None,
                           comment='#')

    all_subaps = list(range(121))
    active_subaps = []
    masked_subaps = all_subaps.copy()

    for index, row in spots_df.iterrows():
        if row[0] != 'SPOT':
            continue

        i = get_subaperture_1d(row[3], row[4])

        active_subaps.append(i)
        masked_subaps.remove(i)

    return all_subaps, active_subaps, masked_subaps


def read_autogain_file(file):
    spots_df = pd.read_csv(file, delim_whitespace=True, header=None,
                           comment='#')

    autogain_params = []

    for index, row in spots_df.iterrows():
        if row[0] != 'EXP':
            continue

        autogain_params.append((row[1], row[2]))

    return autogain_params


def get_dm_flux_map(upsampled=1, upsampling=4, radius_out_factor=1,
                    radius_in_factor=1):
    size = 12 * upsampled * upsampling

    radius_out = 0.5 * size * 4.4 / 4.8 * radius_out_factor  # Pupil radius in px on DM
    radius_in = radius_out * 336.4 / 1200 * radius_in_factor

    y, x = np.mgrid[:size, :size]
    circle = (x - size/2 + 0.5)**2 + (y - size/2 + 0.5)**2
    pupil = np.logical_and(circle <= radius_out**2, circle >= radius_in**2)
    flux = block_reduce(pupil, upsampling, np.mean)

    return flux


def get_wfs_flux_map(upsampling=4, radius_out_factor=1, radius_in_factor=1):
    size = 128 * upsampling

    radius_out = 0.5 * size * 55 / 64 * radius_out_factor  # Pupil radius in px on WFS
    radius_in = radius_out * 336.4 / 1200 * radius_in_factor

    y, x = np.mgrid[:size, :size]
    circle = (x - size/2 + 0.5)**2 + (y - size/2 + 0.5)**2
    pupil = np.logical_and(circle <= radius_out**2, circle >= radius_in**2)
    pupil = block_reduce(pupil, upsampling, np.mean)

    flux = np.zeros((11, 11))

    for i in range(11):
        for j in range(11):
            subap = pupil[9 + i*10:9 + (i+1) * 10, 9 + j*10:9 + (j+1) * 10]
            flux[i, j] = np.mean(subap)

    return flux


def wfs_illumination_fraction(slopes_flux, threshold, subaps_list):
    slopes_flux_flat = slopes_flux.flatten()

    illuminated_subaps = 0

    for i in subaps_list:
        if slopes_flux_flat[i] > threshold:
            illuminated_subaps += 1

    return illuminated_subaps / len(subaps_list)


def subaperture_at_px(x, y):
    if (x+1) % 5 == 0 or (y+1) % 5 == 0:
        return None
    else:
        return get_subaperture_1d((y-5) // 5, (x-5) // 5)


def actuator_at_px(x, y):
    if (x-4) % 5 == 0 and (y-4) % 5 == 0:
        return get_actuator_1d((y-4) // 5, (x-4) // 5)
    else:
        return None


def generate_slopes_mask_from_subaps(masked_subaps, shape=(11, 22)):
    mask = np.zeros(shape, dtype=bool)

    for i in masked_subaps:
        for x, y in subaperture_to_slopes_2d(i):
            mask[x, y] = True

    return mask


def generate_flux_mask_from_subaps(masked_subaps, shape=(11, 11)):
    mask = np.zeros(shape, dtype=bool)

    for i in masked_subaps:
        x, y = get_subaperture_2d(i)
        mask[x, y] = True

    return mask
