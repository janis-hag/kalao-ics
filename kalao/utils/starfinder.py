#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : calibunit
# @Date : 2021-01-02-14-36
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
starfinder.py is part of the KalAO Instrument Control Software (KalAO-ICS).
"""

import math
import time
import warnings
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import scipy.optimize

from astropy import units as u
from astropy import wcs
from astropy.coordinates import AltAz, SkyCoord
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.time import Time
from astropy.utils.exceptions import AstropyWarning

from kalao import euler
from kalao.utils import kmath

import skimage.feature
import skimage.filters

import config


@dataclass
class Star:
    x: float
    y: float
    peak: float
    fwhm_w: float
    fwhm_h: float
    fwhm_angle: float

    fwhm: float = field(init=False)

    def __post_init__(self):
        self.fwhm = np.sqrt(self.fwhm_w * self.fwhm_h)


def find_star(img, min_peak=config.Starfinder.min_peak,
              hw=config.Starfinder.window // 2):
    star = find_stars(img, min_peak=min_peak, hw=hw, num=1)

    if len(star) == 0:
        return None
    else:
        return star[0]


def find_stars(img, min_peak=config.Starfinder.min_peak,
               hw=config.Starfinder.window // 2, num=math.inf):
    stars, bad_pixels = find_stars_and_bad_pixels(img, min_peak=min_peak,
                                                  hw=hw, num=num)

    return stars


def find_stars_and_bad_pixels(img, min_peak=config.Starfinder.min_peak,
                              hw=config.Starfinder.window // 2, num=math.inf):
    img = img.astype(np.float64)

    Y, X = np.mgrid[0:img.shape[0], 0:img.shape[1]]

    img_filtered = skimage.filters.median(img, skimage.morphology.square(3))
    img_filtered = skimage.filters.gaussian(img_filtered, 2)

    mean_filtered, median_filtered, stddev_filtered = sigma_clipped_stats(
        img_filtered)

    img_diff = img - img_filtered
    bad_pixels = np.argwhere((np.abs(img_diff) > 6 * img_diff.std()))

    threshold = median_filtered + max(6 * stddev_filtered, min_peak)
    stars = skimage.feature.peak_local_max(img_filtered, min_distance=1,
                                           exclude_border=0,
                                           threshold_abs=threshold,
                                           num_peaks=num)

    mean, median, stddev = sigma_clipped_stats(img)
    frame_fit = img - median

    stars_fitted = []

    i = 0
    while i < len(stars):
        star_y, star_x = stars[i]

        xs = star_x - hw
        xe = star_x + hw
        ys = star_y - hw
        ye = star_y + hw

        if xs < 0:
            xs = 0

        if xe > img.shape[1]:
            xe = img.shape[1]

        if ys < 0:
            ys = 0

        if ye > img.shape[0]:
            ye = img.shape[0]

        X_cut = X[ys:ye, xs:xe].ravel()
        Y_cut = Y[ys:ye, xs:xe].ravel()
        img_cut = frame_fit[ys:ye, xs:xe].ravel()

        fun = lambda x: np.sqrt(
            np.sum((kmath.gaussian_2d_rotated(X_cut, Y_cut, *x, 0) - img_cut)
                   **2))

        res = scipy.optimize.minimize(
            fun, (star_x, star_y, 1, 1, 0, frame_fit[star_y, star_x]),
            method='L-BFGS-B', bounds=[(star_x - hw, star_x + hw),
                                       (star_y - hw, star_y + hw),
                                       (1, 4 * hw), (1, 4 * hw),
                                       (-np.pi, np.pi), (1, 131072)])

        if not res.success:
            continue

        # Exclude peaks that are within star radius

        x_fitted = res.x[0]
        y_fitted = res.x[1]
        fwhm_x_fitted = res.x[2] * kmath.SIGMA_TO_FWHM
        fwhm_y_fitted = res.x[3] * kmath.SIGMA_TO_FWHM
        theta_fitted = res.x[4]
        peak_fitted = res.x[5]

        j = i + 1
        while j < len(stars):
            dx = stars[j][1] - x_fitted
            dy = stars[j][0] - y_fitted

            cos = np.cos(theta_fitted)
            sin = np.sin(theta_fitted)

            a = fwhm_x_fitted
            b = fwhm_y_fitted

            inside = (cos*dx + sin*dy)**2 / a**2 + (sin*dx +
                                                    cos*dy)**2 / b**2 <= 1

            if inside:
                stars = np.delete(stars, j, axis=0)
            else:
                j += 1

        # Add fit to star list

        stars_fitted.append(
            Star(x_fitted, y_fitted, peak_fitted, fwhm_x_fitted,
                 fwhm_y_fitted, theta_fitted * 180 / np.pi))

        i += 1

    return stars_fitted, bad_pixels


def find_stars_barycenter(img, min_peak=config.Starfinder.min_peak,
                              hw=config.Starfinder.window // 2, num=math.inf):
    hw = 128

    img = img.astype(np.float64)

    Y, X = np.mgrid[0:img.shape[0], 0:img.shape[1]]

    img_filtered = skimage.filters.median(img, skimage.morphology.square(3))
    img_filtered = skimage.filters.gaussian(img_filtered, 2)

    mean_filtered, median_filtered, stddev_filtered = sigma_clipped_stats(
        img_filtered)

    threshold = median_filtered + max(6 * stddev_filtered, min_peak)
    stars = skimage.feature.peak_local_max(img_filtered, min_distance=1,
                                           exclude_border=0,
                                           threshold_abs=threshold,
                                           num_peaks=1)

    mean, median, stddev = sigma_clipped_stats(img)
    frame_fit = img - median

    star_y, star_x = stars[0]

    xs = star_x - hw
    xe = star_x + hw
    ys = star_y - hw
    ye = star_y + hw

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

    flux = np.sum(img_cut)

    x_mean = np.sum(img_cut * X_cut) / flux
    y_mean = np.sum(img_cut * Y_cut) / flux

    x_var = np.sum(img_cut * ((X_cut - x_mean)**2)) / flux
    y_var = np.sum(img_cut * ((Y_cut - y_mean) ** 2)) / flux
    xy_cov = np.sum(img_cut * ((X_cut - x_mean)*(Y_cut - y_mean))) / flux

    eigenvalues, eigenvectors = np.linalg.eig(np.array([[x_var, xy_cov],[xy_cov, y_var]]))

    radius = np.sqrt(np.sum(img_cut * ((X_cut - x_mean)**2 + (Y_cut - y_mean)**2)) / 2 / flux)

    return [Star(x_mean, y_mean, 2*flux/(np.pi*radius**2), np.sqrt(eigenvalues[0]) * kmath.SIGMA_TO_FWHM, np.sqrt(eigenvalues[1]) * kmath.SIGMA_TO_FWHM, np.arctan2(eigenvectors[1,0], eigenvectors[0,0]) * 180/np.pi)], None


def generate_wcs():
    """
    Queries the current telescope coordinates to generate a WCS object.

    :return: WCS object with current telescope coordinates
    """

    # Create a new WCS object.  The number of axes must be set
    # from the start
    w = wcs.WCS(naxis=2)

    # Reference pixel value
    w.wcs.crpix = [config.FLI.center_x, config.FLI.center_y]

    # Pixel scale in degrees
    w.wcs.cdelt = np.array([
        config.FLI.plate_scale / 3600, config.FLI.plate_scale / 3600
    ])

    # RA, DEC at reference
    coord = euler.star_coord()
    w.wcs.crval = [coord.ra.degree, coord.dec.degree]

    # Gnomonic (TAN) projection
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

    # Pixel coordinates transformation matrix
    # parang = parallactic_angle() * np.pi/180
    # w.wcs.pc = np.array([[np.cos(parang), -np.sin(parang)],
    #                      [np.sin(parang), np.cos(parang)]])
    # TODO: check if mirroring needed

    # w.wcs.radesys = '???'
    # w.wcs.equinox = 2000.0

    return w


def parallactic_angle(dt=None, coord=None):
    location = euler.observing_location()

    if isinstance(dt, datetime):
        astro_time = Time(dt, scale='utc', location=location)
        print(f'Using custom date: {astro_time}')

    else:
        astro_time = Time(datetime.utcnow(), scale='utc', location=location)

    if isinstance(coord, SkyCoord):
        print(f'Using custom coord: {coord}')
    else:
        coord = euler.star_coord()

    r2d = 180 / np.pi
    d2r = np.pi / 180

    geolat_rad = config.Euler.latitude * d2r

    lst_ra = astro_time.sidereal_time('mean').hour * 15 * d2r  #(15./3600)*d2r

    ha_rad = lst_ra - coord.ra.rad
    dec_rad = coord.dec.rad

    # ha_deg=(float(hdr['LST'])*15./3600)-ra_deg

    # VLT TCS formula
    f1 = float(np.cos(geolat_rad) * np.sin(ha_rad))
    f2 = float(
        np.sin(geolat_rad) * np.cos(dec_rad) -
        np.cos(geolat_rad) * np.sin(dec_rad) * np.cos(ha_rad))
    parang = -r2d * np.arctan2(-f1, f2)  # Sign depends on focus

    print('parang - VLT TCS formula', parang)

    # Using astropy

    altaz_frame = AltAz(location=location, obstime=astro_time)
    coord_alt_az = coord.transform_to(altaz_frame)
    probe = coord_alt_az.spherical_offsets_by(0 * u.arcsec, 0.1 *
                                              u.arcsec).transform_to('icrs')
    pa = coord_alt_az.position_angle(probe)

    print('parang - Astropy', pa.deg)

    return parang


if __name__ == "__main__":
    import sys

    import matplotlib.patches as patches
    import matplotlib.pyplot as plt

    if len(sys.argv) == 1:
        rng = np.random.default_rng()

        frame = np.zeros((1024, 1024), dtype=np.float32)
        Y, X = np.mgrid[0:1024, 0:1024]

        # Add stars
        for i in range(5):
            x = rng.uniform(50, 1024 - 50)
            y = rng.uniform(50, 1024 - 50)
            peak = rng.uniform(100, 3000)
            stddev = rng.uniform(2, 30)

            frame += kmath.gaussian_2d_rotated(X, Y, x, y, stddev, stddev, 0/180*np.pi,
                                               peak)

        frame = rng.poisson(frame).astype(np.float64)

        # Add dead pixels
        for i in range(10):
            x = round(rng.uniform(50, 1024 - 50))
            y = round(rng.uniform(50, 1024 - 50))

            frame[y, x] = 0

        # Add stuck pixels
        for i in range(10):
            x = round(rng.uniform(50, 1024 - 50))
            y = round(rng.uniform(50, 1024 - 50))

            frame[y, x] = 65535

        # Add hot pixels
        for i in range(10):
            x = round(rng.uniform(50, 1024 - 50))
            y = round(rng.uniform(50, 1024 - 50))
            v = round(rng.uniform(10, 4000))

            frame[y, x] += v

        frame += rng.normal(1000, 20, size=frame.shape)

        frame = np.clip(np.rint(frame), 0, 2**16 - 1).astype(np.uint16)
        frames = [frame]
    else:
        frames = []
        for i in range(1, len(sys.argv)):
            frames.append(fits.getdata(sys.argv[i]))

    for i, frame in enumerate(frames):
        if i + 1 < len(sys.argv):
            title = f'Frame {i} - {sys.argv[i+1]}'
        else:
            title = f'Frame {i}'

        print(title)

        plt.figure()
        plt.title(title)
        fig = plt.gcf()
        ax = fig.gca()

        plt.imshow(frame, norm='log'
                   )  # , vmin=np.nanmin(frame_nan), vmax=np.nanmax(frame_nan))

        start = time.monotonic()
        stars, bad_pixels = find_stars_and_bad_pixels(frame)
        print('Time to find stars:', time.monotonic() - start)

        for star in stars:
            plt.plot(star.x, star.y, 'r+')
            ax.add_patch(
                patches.Ellipse((star.x, star.y), star.fwhm_w, star.fwhm_h,
                                angle=star.fwhm_angle, edgecolor='r',
                                facecolor='#ffffff00'))

        start = time.monotonic()
        stars, bad_pixels = find_stars_barycenter(frame)
        print('Time to find stars:', time.monotonic() - start)

        for star in stars:
            plt.plot(star.x, star.y, 'b+')
            ax.add_patch(
                patches.Ellipse((star.x, star.y), star.fwhm_w, star.fwhm_h,
                                angle=star.fwhm_angle, edgecolor='b',
                                facecolor='#ffffff00'))

        # frame_nan = frame.astype(np.float64)
        # frame_nan[bad_pixels] = np.nan

        # plt.plot(bad_pixels[:, 1], bad_pixels[:, 0], 'g+')

    plt.show()
