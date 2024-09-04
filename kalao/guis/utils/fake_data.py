#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import math

import numpy as np
from scipy import ndimage

from astropy.nddata import block_reduce, block_replicate

from kalao.common import kmath, ktools, zernike

import config

rng = np.random.default_rng()

#TODO: use streams_info in func below


def tiptilt(nb_points=1, seed=np.zeros((2, )), sigma=0.01, leak=0.01):
    tiptilt = [seed]

    for i in range(nb_points):
        tiptilt.append(rng.normal(tiptilt[-1] * (1-leak), sigma))

    del tiptilt[0]

    if nb_points == 1:
        return tiptilt[0]
    else:
        return tiptilt


def wfs_frame(
    bias=2000,
    readoutnoise=20,
    flux=5000,
    tiptilt=np.zeros((2, )),
    dmdisp=zernike.generate_pattern([0], (12, 12)),
    illumination='telescope',
    upsampling=4,
):
    frame = np.zeros((64 * upsampling, 64 * upsampling), dtype=np.float64)

    if illumination == 'telescope':
        flux_map = ktools.get_wfs_flux_map()
    else:
        flux_map = ktools.get_wfs_flux_map(radius_in_factor=0,
                                           radius_out_factor=1.1)

    ttm_tip_px = tiptilt[0] * config.TTM.plate_scale / config.WFS.plate_scale
    ttm_tilt_px = tiptilt[1] * config.TTM.plate_scale / config.WFS.plate_scale

    slopes_px = zernike.slopes_from_pattern_interp(
        dmdisp) * config.DM.plate_scale / config.WFS.plate_scale

    sigma = 1.06 / kmath.SIGMA_TO_FWHM
    intensity = 2 * flux / (np.pi * 4 * sigma**2)

    sigma *= upsampling
    hwindow = math.ceil(3 * sigma)

    y, x = np.mgrid[0:2 * hwindow, 0:2 * hwindow]

    for i in range(11):
        for j in range(11):
            if flux_map[i, j] < 1e-2:
                continue

            tilt_dm_px = slopes_px.data[j, i]
            tip_dm_px = slopes_px.data[j, i + 11]

            psf_y = (5*j + 7 + ttm_tilt_px + tilt_dm_px) * upsampling
            psf_x = (5*i + 7 + ttm_tip_px + tip_dm_px) * upsampling

            psf_y_f, psf_y_i = math.modf(psf_y)
            psf_x_f, psf_x_i = math.modf(psf_x)

            psf_y_i = int(psf_y_i)
            psf_x_i = int(psf_x_i)

            mu_y = hwindow + psf_y_f - 0.5
            mu_x = hwindow + psf_x_f - 0.5

            A = intensity * flux_map[i, j]

            frame[psf_y_i - hwindow:psf_y_i + hwindow, psf_x_i -
                  hwindow:psf_x_i + hwindow] += kmath.gaussian_2d_rotated(
                      x, y, mu_x, mu_y, sigma, sigma, 0, A, 0)

    # Reduce to final size with photon shot noise
    frame = rng.poisson(block_reduce(frame, upsampling,
                                     func=np.mean)).astype(np.float64)

    # Add electronic noise
    frame += rng.normal(bias, readoutnoise, size=frame.shape)

    # Clip as unit16
    return (np.clip(np.rint(frame), 0, 2**16 - 1) - bias).astype(np.int32)


def slopes(wfs_frame):
    _, subapertures = ktools.get_roi_and_subapertures(wfs_frame)

    slopes = np.zeros((11, 22))

    for i, subap in enumerate(subapertures):
        j, k = ktools.get_subaperture_2d(i)

        if math.isclose(np.sum(subap), 0):
            x, y = 0, 0
        else:
            x, y = np.clip(
                np.array(ndimage.center_of_mass(subap)) - [1.5, 1.5], -2, 2)

        slopes[k, j] = x
        slopes[k, j + 11] = y

    return slopes


def flux(wfs_frame):
    _, subapertures = ktools.get_roi_and_subapertures(wfs_frame)

    flux = np.zeros((11, 11))

    for i, subap in enumerate(subapertures):
        j, k = ktools.get_subaperture_2d(i)

        flux[k, j] = np.sum(subap)

    return flux


def dmdisp(zernike_coeffs=None, orders=15):
    if zernike_coeffs is None:
        zernike_coeffs = rng.normal(0, 0.1, orders)
        zernike_coeffs[0] = 0

    return zernike.generate_pattern(zernike_coeffs, (12, 12))


def camera_frame(
    bias=1070,
    readoutnoise=7,
    psf_x=config.Camera.center_x,
    psf_y=config.Camera.center_y,
    flux=2**15,
    tiptilt=np.zeros((2, )),
    dmdisp=zernike.generate_pattern([0], (12, 12)),
    illumination='telescope',
):
    frame = np.zeros((1024, 1024), dtype=np.float64)

    ttm_tip_px = tiptilt[0] * config.TTM.plate_scale / config.Camera.plate_scale
    ttm_tilt_px = tiptilt[1] * config.TTM.plate_scale / config.Camera.plate_scale

    slopes_px = zernike.slopes_from_pattern_interp(
        dmdisp) * config.DM.plate_scale / config.Camera.plate_scale

    dm_tilt_px = slopes_px[0:11, 0:11].mean()
    dm_tip_px = slopes_px[0:11, 11:22].mean()

    psf_y = (psf_y + ttm_tilt_px + dm_tilt_px)
    psf_x = (psf_x + ttm_tip_px + dm_tip_px)

    psf_y_f, psf_y_i = math.modf(psf_y)
    psf_x_f, psf_x_i = math.modf(psf_x)

    psf_y_i = int(psf_y_i)
    psf_x_i = int(psf_x_i)

    dmdisp += zernike.generate_pattern([
        0, (-dm_tip_px + psf_x_f) *
        config.Camera.plate_scale / config.DM.plate_scale,
        (-dm_tilt_px + psf_y_f) * config.Camera.plate_scale /
        config.DM.plate_scale
    ], (12, 12))

    upsampling = 3
    hwindow = 2**5

    if illumination == 'telescope':
        flux_map = ktools.get_dm_flux_map(upsampled=upsampling)
    else:
        flux_map = ktools.get_dm_flux_map(upsampled=upsampling,
                                          radius_in_factor=0,
                                          radius_out_factor=1.1)

    flux_map /= np.sum(flux_map)

    phase = 2 * np.pi * (dmdisp*2) / 0.635
    phase = block_replicate(phase, upsampling, conserve_sum=False)

    field = np.sqrt(flux_map) * np.exp(1j * phase)

    pad = (2*hwindow - flux_map.shape[0]) // 2
    field_ = np.pad(field, ((pad, pad), (pad, pad)))

    psf = flux * np.abs(np.fft.fftshift(np.fft.fft2(field_, norm='ortho')))**2

    frame[psf_y_i - hwindow:psf_y_i + hwindow,
          psf_x_i - hwindow:psf_x_i + hwindow] += psf

    # Reduce to final size with photon shot noise
    frame = rng.poisson(frame).astype(np.float64)

    # Add electronic noise
    frame += rng.normal(bias, readoutnoise, size=frame.shape)

    # Clip as unit16
    return np.clip(np.rint(frame), 0, 2**16 - 1).astype(np.uint16)


def slopes_params(slopes):
    tilt = slopes[0:11, 0:11]
    tip = slopes[0:11, 11:22]

    return {
        'slope_x_avg': tip.mean(),
        'slope_y_avg': tilt.mean(),
        'residual_rms': np.sqrt((tip**2 + tilt**2).mean())
    }


def flux_params(flux):
    return {'flux_avg': flux.mean(), 'flux_max': flux.max()}
