#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : calibunit
# @Date : 2021-01-02-14-36
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
starfinder.py is part of the KalAO Instrument Control Software (KalAO-ICS).
"""

import sys

import numpy as np
import scipy.optimize

from astropy.stats import sigma_clipped_stats

import skimage.feature
import skimage.filters

from kalao.utils import kmath

from kalao.definitions.dataclasses import Star

import config


def find_star(img: np.ndarray, min_peak: float = config.Starfinder.min_peak,
              hw: int = config.Starfinder.window // 2,
              method: str = 'gaussian_fit') -> Star | None:
    star = find_stars(img, min_peak=min_peak, hw=hw, num=1, method=method)

    if len(star) == 0:
        return None
    else:
        return star[0]


def find_stars(img: np.ndarray, min_peak: float = config.Starfinder.min_peak,
               hw: int = config.Starfinder.window // 2, num: int = sys.maxsize,
               method: str = 'gaussian_fit') -> list[Star]:
    stars, bad_pixels = find_stars_and_bad_pixels(img, min_peak=min_peak,
                                                  hw=hw, num=num,
                                                  method=method)

    return stars


def find_stars_and_bad_pixels(img: np.ndarray,
                              min_peak: float = config.Starfinder.min_peak,
                              hw: int = config.Starfinder.window // 2,
                              num: int = sys.maxsize,
                              method: str = 'gaussian_fit'
                              ) -> tuple[list[Star], np.ndarray]:
    img = img.astype(np.float64)

    Y, X = np.mgrid[0:img.shape[0], 0:img.shape[1]]

    img_filtered = skimage.filters.median(img, skimage.morphology.square(3))
    img_filtered = skimage.filters.gaussian(img_filtered, 2)

    mean, median, stddev = sigma_clipped_stats(img_filtered)

    img_diff = img - img_filtered
    bad_pixels = np.argwhere((np.abs(img_diff) > 6 * img_diff.std()))

    threshold = median + max(6 * stddev, min_peak)
    peaks = skimage.feature.peak_local_max(img_filtered, min_distance=1,
                                           exclude_border=0,
                                           threshold_abs=threshold,
                                           num_peaks=num)

    mean, median, stddev = sigma_clipped_stats(img)
    frame_fit = img - median

    stars_fitted = []

    if method == 'moments':
        hw = 128

    i = 0
    while i < len(peaks):
        peak_y, peak_x = peaks[i]

        xs = peak_x - hw
        xe = peak_x + hw
        ys = peak_y - hw
        ye = peak_y + hw

        if xs < 0:
            xs = 0

        if xe > img.shape[1]:
            xe = img.shape[1]

        if ys < 0:
            ys = 0

        if ye > img.shape[0]:
            ye = img.shape[0]

        X_cut = X[ys:ye, xs:xe]
        Y_cut = Y[ys:ye, xs:xe]
        img_cut = frame_fit[ys:ye, xs:xe]

        if method == 'gaussian_fit':
            star = _star_gaussian_fit(X_cut, Y_cut, img_cut, peak_x, peak_y,
                                      frame_fit[peak_y, peak_x], hw)
        elif method == 'moments':
            star = _star_moments(X_cut, Y_cut, img_cut)
        else:
            raise Exception(f'Unknown method {method}')

        if star is None:
            continue

        # Exclude peaks that are within star radius

        j = i + 1
        while j < len(peaks):
            dx = peaks[j][1] - star.x
            dy = peaks[j][0] - star.y

            cos = np.cos(star.fwhm_angle * 180 / np.pi)
            sin = np.sin(star.fwhm_angle * 180 / np.pi)

            a = star.fwhm_w
            b = star.fwhm_h

            inside = (cos*dx + sin*dy)**2 / a**2 + (sin*dx +
                                                    cos*dy)**2 / b**2 <= 1

            if inside:
                peaks = np.delete(peaks, j, axis=0)
            else:
                j += 1

        # Add fit to star list

        stars_fitted.append(star)

        i += 1

    return stars_fitted, bad_pixels


def _star_gaussian_fit(X: np.ndarray, Y: np.ndarray, img: np.ndarray,
                       peak_x: float, peak_y: float, peak_value: float,
                       hw: int) -> Star | None:
    X = X.ravel()
    Y = Y.ravel()
    img = img.ravel()

    def gaussian(t):
        return np.sqrt(
            np.sum((kmath.gaussian_2d_rotated(X, Y, *t, 0) - img)**2))

    res = scipy.optimize.minimize(
        gaussian, (peak_x, peak_y, 1, 1, 0, peak_value), method='L-BFGS-B',
        bounds=[(peak_x - hw, peak_x + hw), (peak_y - hw, peak_y + hw),
                (1, 4 * hw), (1, 4 * hw), (-np.pi, np.pi), (1, 131072)])

    if not res.success:
        return None

    x_mean = res.x[0]
    y_mean = res.x[1]
    fwhm_w = res.x[2] * kmath.SIGMA_TO_FWHM
    fwhm_h = res.x[3] * kmath.SIGMA_TO_FWHM
    fwhm_angle = res.x[4] * 180 / np.pi
    peak = res.x[5]

    return Star(x=x_mean, y=y_mean, peak=peak, fwhm_w=fwhm_w, fwhm_h=fwhm_h,
                fwhm_angle=fwhm_angle)


def _star_moments(X: np.ndarray, Y: np.ndarray, img: np.ndarray) -> Star:
    flux = np.sum(img)

    x_mean = np.sum(img * X) / flux
    y_mean = np.sum(img * Y) / flux

    x_var = np.sum(img * ((X - x_mean)**2)) / flux
    y_var = np.sum(img * ((Y - y_mean)**2)) / flux
    xy_cov = np.sum(img * ((X-x_mean) * (Y-y_mean))) / flux

    eigenvalues, eigenvectors = np.linalg.eig(
        np.array([[x_var, xy_cov], [xy_cov, y_var]]))

    fwhm_w = np.sqrt(eigenvalues[0]) * kmath.SIGMA_TO_FWHM
    fwhm_h = np.sqrt(eigenvalues[1]) * kmath.SIGMA_TO_FWHM
    fwhm_angle = np.arctan2(eigenvectors[1, 0], eigenvectors[0,
                                                             0]) * 180 / np.pi
    fwhm = np.sqrt(fwhm_w * fwhm_h)
    peak = 2 * flux / (np.pi * (fwhm / 2)**2)

    return Star(x=x_mean, y=y_mean, peak=peak, fwhm_w=fwhm_w, fwhm_h=fwhm_h,
                fwhm_angle=fwhm_angle)
