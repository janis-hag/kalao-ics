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

from kalao import database, euler
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
                                           exclude_border=hw,
                                           threshold_abs=threshold,
                                           num_peaks=num)

    mean, median, stddev = sigma_clipped_stats(img)
    frame_fit = img - median

    stars_fitted = []

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', AstropyWarning)

        i = 0
        while i < len(stars):
            star_y, star_x = stars[i]

            X_fit = X[star_y - hw:star_y + hw, star_x - hw:star_x + hw].ravel()
            Y_fit = Y[star_y - hw:star_y + hw, star_x - hw:star_x + hw].ravel()
            Z_fit = frame_fit[star_y - hw:star_y + hw,
                              star_x - hw:star_x + hw].ravel()

            fun = lambda x: np.sqrt(
                np.sum((kmath.gaussian_2d_rotated(X_fit, Y_fit, *x, 0) - Z_fit)
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


def find_star_fits(image_path):
    """
    Finds the position of a star spot in an image taken with the FLI camera

    :param image_path: path for the image to be centered (String)

    :return: center of the star or (-1, -1) if an error has occurred. (float, float)
    """

    hdu_list = fits.open(image_path)
    hdu_list.info()
    image = hdu_list[0].data
    hdu_list.close()

    x_star, y_star, peak, fwhm = find_star(image)

    database.store(
        'obs', {
            'psf_file': image_path.name,
            'psf_x': x_star,
            'psf_y': y_star,
            'psf_peak': peak,
            'psf_fwhm': fwhm
        })

    return x_star, y_star, peak, fwhm


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

            frame += kmath.gaussian_2d_rotated(X, Y, x, y, stddev, stddev, 0,
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

        start = time.monotonic()
        stars, bad_pixels = find_stars_and_bad_pixels(frame)
        print('Time to find stars:', time.monotonic() - start)

        frame_nan = frame.astype(np.float64)
        frame_nan[bad_pixels] = np.nan

        plt.imshow(frame, norm='log'
                   )  #, vmin=np.nanmin(frame_nan), vmax=np.nanmax(frame_nan))

        fig = plt.gcf()
        ax = fig.gca()

        for star in stars:
            plt.plot(star.x, star.y, 'r+')
            ax.add_patch(
                patches.Ellipse((star.x, star.y), star.fwhm_w, star.fwhm_h,
                                angle=star.fwhm_angle, edgecolor='r',
                                facecolor='#ffffff00'))

        # plt.plot(bad_pixels[:, 1], bad_pixels[:, 0], 'g+')

    plt.show()
