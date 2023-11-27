#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import builtins
import math
import random
from datetime import datetime, timedelta

import numpy as np
from scipy import ndimage

from astropy.nddata import block_reduce

from kalao.utils import image, kalao_math, kalao_time, kalao_tools, zernike

from kalao.definitions.enums import StrEnum

import config

rng = np.random.default_rng()

#TODO: use streams_info in func below


def fake_streams():
    streams = {}

    # Fake WFS
    nuvu_stream = nuvu_frame()

    streams["nuvu_stream"] = {
        "data": nuvu_stream.flatten(),
        "width": nuvu_stream[1],
        "height": nuvu_stream[0],
        "min": nuvu_stream.min(),
        "max": nuvu_stream.max(),
        "min_th": min,
        "max_th": max,
    }

    # Fake WFS flux
    shwfs_slopes_flux = flux(nuvu_stream)

    streams["shwfs_slopes_flux"] = {
        "data": shwfs_slopes_flux.flatten(),
        "width": shwfs_slopes_flux[1],
        "height": shwfs_slopes_flux[0],
        "min": shwfs_slopes_flux.min(),
        "max": shwfs_slopes_flux.max(),
        "min_th": min,
        "max_th": max,
    }

    # Fake slopes
    shwfs_slopes = slopes(nuvu_stream)

    streams["shwfs_slopes"] = {
        "data": shwfs_slopes.flatten(),
        "width": shwfs_slopes[1],
        "height": shwfs_slopes[0],
        "min": shwfs_slopes.min(),
        "max": shwfs_slopes.max(),
        "min_th": min,
        "max_th": max,
    }

    # Fake focus on the DM
    dm01disp = dm()

    streams["dm01disp"] = {
        "data": dm01disp.flatten(),
        "width": dm01disp[1],
        "height": dm01disp[0],
        "min": dm01disp.min(),
        "max": dm01disp.max(),
        "min_th": min,
        "max_th": max,
    }

    # Fake mode coefficients
    rows = 1
    cols = 121
    min = -1.75
    max = 1.75
    noise = 0.03
    aol1_modeval = [0] * rows * cols

    sign = 1
    tau = 3

    # yapf: enable
    for i in range(cols):
        aol1_modeval[i] = sign * ((max-min) / 2 - 2*noise) * math.exp(
            -i / tau) + (max+min) / 2 + random.gauss(0, noise)
        sign *= -1
    # yapf: disable

    streams["aol1_modeval"] = {
            "data": aol1_modeval,
            "width": cols,
            "height": rows,
            "min": min,
            "max": max,
            "min_th": min,
            "max_th": max,
    }

    return streams


def fake_tip_tilt(nb_points = 1):
    min = -0.25
    max = 0.25

    time_now = kalao_time.now()

    telemetry = {}
    keys = ["pi_tip", "pi_tilt"]

    for key in keys:
        telemetry[key] = []

        for i in range(nb_points):
            telemetry[key].append({'value': random.gauss(min, max) , 'timestamp': time_now - timedelta(seconds=i)})

    return telemetry

def tiptilt(nb_points = 1, seed=np.zeros((2,)), sigma = 0.01, leak=0.01):
    tiptilt = [seed]

    for i in range(nb_points):
        tiptilt.append(rng.normal(tiptilt[-1]*(1-leak), sigma))


    del tiptilt[0]

    if nb_points == 1:
        return tiptilt[0]
    else:
        return tiptilt


def nuvu_frame(bias = 2000, readoutnoise = 20, flux = 5000, tiptilt=np.zeros((2,)), dmdisp=np.zeros((12,12)), upsampling=4):
    frame = np.zeros((64*upsampling, 64*upsampling))
    x, y = np.mgrid[0:frame.shape[0], 0:frame.shape[1]].astype(np.float32)

    tip_px = tiptilt[0] * config.TTM.plate_scale / config.WFS.plate_scale
    tilt_px = tiptilt[1] * config.TTM.plate_scale / config.WFS.plate_scale

    slopes_px = zernike.slopes_from_pattern_interp(dmdisp) * config.DM.plate_scale / config.WFS.plate_scale

    #TODO: more correct
    sigma = 1

    intensity = 2 * flux / (np.pi * 4*sigma**2)

    sigma = sigma * upsampling

    # yapf: disable
    for i in range(11):
        for j in range(11):
            tip_dm_px = slopes_px[j, i]
            tilt_dm_px = slopes_px[j, i+11]

            mu_x = (5 * i + 3 + 4 + tip_px + tip_dm_px)*upsampling - 0.5
            mu_y = (5 * j + 3 + 4 + tilt_px + tilt_dm_px)*upsampling - 0.5

            A = intensity * config.AO.flux_map[i,j]

            frame += kalao_math.gaussian_2d_rotated(x, y, mu_x, mu_y, sigma, sigma, 0, A, 0)

    # Reduce with final size with photon shot noise
    frame = rng.poisson(block_reduce(frame, upsampling, func=np.mean)).astype(np.float64)

    # Add electronic noise
    frame += rng.normal(bias, readoutnoise, size=frame.shape)

    # Clip as unit16
    return np.clip(np.rint(frame), 0, 2 ** 16 - 1) - bias

def slopes(nuvu_fr = None):
    if nuvu_fr is None:
        nuvu_fr = nuvu_frame()

    _, subapertures = kalao_tools.get_roi_and_subapertures(nuvu_fr)

    slopes = np.zeros((11, 22))

    for i, subap in enumerate(subapertures):
        j, k = kalao_tools.get_subaperture_2d(i)

        x, y = np.clip(np.array(ndimage.center_of_mass(subap)) - [1.5, 1.5], -2, 2)

        slopes[k, j] = x
        slopes[k, j+11] = y

    mask = kalao_tools.generate_slopes_mask_from_subaps(config.AO.masked_subaps)

    return np.ma.masked_array(slopes, mask=mask, fill_value=0)


def flux(nuvu_fr = None):
    if nuvu_fr is None:
        nuvu_fr = nuvu_frame()

    _, subapertures = kalao_tools.get_roi_and_subapertures(nuvu_fr)

    flux = np.zeros((11, 11))

    for i, subap in enumerate(subapertures):
        j, k = kalao_tools.get_subaperture_2d(i)

        flux[k, j] = np.sum(subap)

    mask = kalao_tools.generate_flux_mask_from_subaps(config.AO.masked_subaps)

    return np.ma.masked_array(flux, mask=mask, fill_value=0)


def dm(zernike_coeffs = None, orders = 15):
    if zernike_coeffs is None:
        zernike_coeffs = np.zeros((orders,))

        for i in range(1,orders):
            zernike_coeffs[i] = rng.normal(0, 0.05)

    pattern = zernike.generate_pattern(zernike_coeffs, (12,12))

    x = np.arange(-5.5, 6.5)
    y = np.arange(-5.5, 6.5)

    X, Y = np.meshgrid(x,y)

    mask = X**2 + Y**2 > 6**2

    return np.ma.masked_array(pattern, mask=mask, fill_value=0)


def fli_frame(bias = 1070, readoutnoise = 7, psf_x = config.FLI.center_x, psf_y = config.FLI.center_y, fwhm = 10, intensity = 2**15, tiptilt=np.zeros((2,)), dmdisp=np.zeros((12,12)), upsampling = 1):
    frame = np.zeros((1024 * upsampling, 1024 * upsampling))
    x, y = np.mgrid[0:frame.shape[0], 0:frame.shape[1]].astype(np.float32)

    sigma = fwhm / kalao_math.SIGMA_TO_FWHM

    tip_px = tiptilt[0] * config.TTM.plate_scale / config.FLI.plate_scale
    tilt_px = tiptilt[1] * config.TTM.plate_scale / config.FLI.plate_scale

    slopes_px = zernike.slopes_from_pattern_interp(dmdisp) * config.DM.plate_scale / config.FLI.plate_scale
    slopes_params_px = slopes_params(slopes_px)

    psf_x += tip_px + slopes_params_px['tip']
    psf_y += tilt_px + slopes_params_px['tilt']

    psf_x *= upsampling
    psf_y *= upsampling
    sigma *= upsampling

    frame += kalao_math.gaussian_2d_rotated(x, y, psf_y, psf_x, sigma, sigma, 0, intensity, 0)

    # Reduce with final size with photon shot noise
    frame = rng.poisson(block_reduce(frame, upsampling, func=np.mean)).astype(np.float64)

    # Add electronic noise
    frame += rng.normal(bias, readoutnoise, size=frame.shape)

    # Clip as unit16
    return np.clip(np.rint(frame), 0, 2 ** 16 - 1)


def slopes_params(slopes):
    tip = slopes[0:11, 0:11]
    tilt = slopes[0:11, 11:22]

    return {
        'tip': tip.mean(),
        'tilt': tilt.mean(),
        'residual': np.sqrt((tip**2 + tilt**2).mean())
    }


def flux_params(flux):
    return {
        'flux_subaperture_avg': flux.mean(),
        'flux_subaperture_brightest': flux.max()
    }


def fake_all_last_telemetry():

    timestamp = kalao_time.now()

    telemetry = {}

    # NuVu
    telemetry["nuvu_temp_ccd"] = [{
            "timestamp": timestamp,
            "value": -60 + random.gauss(0, 0.05)
    }]
    telemetry["nuvu_temp_controller"] = [{
            "timestamp": timestamp,
            "value": 45 + random.gauss(0, 0.05)
    }]
    telemetry["nuvu_temp_power_supply"] = [{
            "timestamp": timestamp,
            "value": 45 + random.gauss(0, 0.05)
    }]
    telemetry["nuvu_temp_fpga"] = [{
            "timestamp": timestamp,
            "value": 50 + random.gauss(0, 0.05)
    }]
    telemetry["nuvu_temp_heatsink"] = [{
            "timestamp": timestamp,
            "value": 15 + random.gauss(0, 0.05)
    }]
    telemetry["nuvu_emgain"] = [{"timestamp": timestamp, "value": 200}]
    telemetry["nuvu_exposuretime"] = [{"timestamp": timestamp, "value": 0.5}]

    # Slopes
    telemetry["slopes_flux_subaperture"] = [{
            "timestamp": timestamp,
            "value": 2**16 - 1 - 200 + random.gauss(0, 200)
    }]
    telemetry["slopes_residual"] = [{
            "timestamp": timestamp,
            "value": 0.05 + random.gauss(0, 0.02)
    }]

    # Tip-Tilt
    telemetry["pi_tip"] = [{
            "timestamp": timestamp,
            "value": 0 + random.gauss(0, 0.5)
    }]
    telemetry["pi_tilt"] = [{
            "timestamp": timestamp,
            "value": 0 + random.gauss(0, 0.5)
    }]

    return telemetry


def fake_latest_obs_entry():
    time_string = datetime.today().isoformat(timespec='milliseconds')
    key_name = 'TEST'
    record_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua'
    formated_entry_text = time_string + ' ' + key_name + ': ' + record_text

    return formated_entry_text


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    streams = fake_streams()

    fig, axs = plt.subplots(2, 3)

    def _add_stream(i, j, name):
        axs[i, j].imshow(
                np.array(streams[name]["data"]).reshape(
                        streams[name]["height"], streams[name]["width"]),
                cmap='gray')

    _add_stream(0, 0, "nuvu_stream")
    _add_stream(0, 1, "shwfs_slopes_flux")
    _add_stream(1, 0, "shwfs_slopes")
    _add_stream(1, 1, "dm01disp")

    fli = fli_frame()

    axs[0, 2].imshow(fli, cmap='gray')
    axs[1, 2].imshow(image.cut(fli, (256,256)), cmap='gray')

    plt.show()
