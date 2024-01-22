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
from datetime import datetime

import numpy as np

from astropy import units as u
from astropy import wcs
from astropy.coordinates import AltAz, SkyCoord
from astropy.io import fits
from astropy.modeling import fitting, models
from astropy.stats import sigma_clipped_stats
from astropy.time import Time
from astropy.utils.exceptions import AstropyWarning

from kalao import database, euler

import skimage.feature
import skimage.filters

import config


def find_star(img, min_peak=config.Starfinder.min_peak,
              hw=config.Starfinder.window // 2):
    star = find_stars(img, min_peak=min_peak, hw=hw, num=1)

    if len(star) == 0:
        return np.nan, np.nan, np.nan, np.nan
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

        for star_y, star_x in stars:
            model_init = models.Gaussian2D(x_mean=star_x, y_mean=star_y,
                                           amplitude=frame_fit[star_y, star_x])
            fitter = fitting.LevMarLSQFitter()
            model = fitter(
                model_init, X[star_y - hw:star_y + hw,
                              star_x - hw:star_x + hw],
                Y[star_y - hw:star_y + hw, star_x - hw:star_x + hw],
                frame_fit[star_y - hw:star_y + hw, star_x - hw:star_x + hw])

            if not star_x - hw <= model.x_mean.value <= star_x + hw:
                continue

            if not star_y - hw <= model.y_mean.value <= star_y + hw:
                continue

            if np.sqrt(model.x_fwhm * model.y_fwhm) > 2 * hw:
                continue

            stars_fitted.append(
                (model.x_mean.value, model.y_mean.value, model.amplitude.value,
                 np.sqrt(model.x_fwhm * model.y_fwhm)))

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

        gaussian = models.Gaussian2D()

        # Add stars
        for i in range(5):
            x = rng.uniform(50, 1024 - 50)
            y = rng.uniform(50, 1024 - 50)
            peak = rng.uniform(100, 3000)
            stddev = rng.uniform(2, 30)

            frame += gaussian.evaluate(X, Y, peak, x, y, stddev, stddev, 0)

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

        for x, y, peak, fwhm in stars:
            plt.plot(x, y, 'r+')
            ax.add_patch(
                plt.Circle((x, y), fwhm / 2, edgecolor='r',
                           facecolor='#ffffff00'))

        plt.plot(bad_pixels[:, 1], bad_pixels[:, 0], 'g+')

    plt.show()
