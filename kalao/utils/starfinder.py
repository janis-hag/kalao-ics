#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : calibunit
# @Date : 2021-01-02-14-36
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Utilities for star and laser centering.

starfinder.py is part of the KalAO Instrument Control Software (KalAO-ICS).
"""
import math
import time
from datetime import datetime

import numpy as np

from astropy import units as u
from astropy import wcs
from astropy.coordinates import AltAz, SkyCoord
from astropy.io import fits
from astropy.modeling import fitting, models
from astropy.stats import sigma_clipped_stats
from astropy.time import Time
from photutils.detection import DAOStarFinder

from kalao import database, euler

import skimage

import config


def find_star(img, peak_min=100, hw=20):
    star = find_stars(img, peak_min=peak_min, hw=hw, num=1)

    if len(star) == 0:
        return np.nan, np.nan, np.nan, np.nan
    else:
        return star[0]


def find_stars(img, peak_min=100, hw=20, num=math.inf):
    stars, bad_pixels = find_stars_and_bad_pixels(img, peak_min=peak_min,
                                                  hw=hw, num=num)

    return stars


def find_stars_and_bad_pixels(img, peak_min=100, hw=20, num=math.inf):
    Y, X = np.mgrid[0:img.shape[0], 0:img.shape[1]]

    img_filtered = skimage.filters.median(img, skimage.morphology.square(3))
    img_filtered = skimage.filters.gaussian(img_filtered, 2)

    mean_filtered, median_filtered, stddev_filtered = sigma_clipped_stats(
        img_filtered)

    img_diff = img - img_filtered
    bad_pixels = np.argwhere((np.abs(img_diff) > 6 * img_diff.std()))

    threshold = median_filtered + max(6 * stddev_filtered, peak_min)
    stars = skimage.feature.peak_local_max(img_filtered, min_distance=1,
                                           threshold_abs=threshold,
                                           num_peaks=num)

    mean, median, stddev = sigma_clipped_stats(img)
    frame_fit = img - median

    stars_fitted = []
    for star_y, star_x in stars:
        if [star_y, star_x] in bad_pixels:
            continue

        gaussian_init = models.Gaussian2D(x_mean=star_x, y_mean=star_y,
                                          amplitude=frame_fit[star_y, star_x])
        fitter = fitting.LevMarLSQFitter()
        gaussian = fitter(
            gaussian_init, X[star_y - hw:star_y + hw, star_x - hw:star_x + hw],
            Y[star_y - hw:star_y + hw, star_x - hw:star_x + hw],
            frame_fit[star_y - hw:star_y + hw, star_x - hw:star_x + hw])

        stars_fitted.append((gaussian.x_mean.value, gaussian.y_mean.value,
                             gaussian.amplitude.value,
                             np.sqrt(gaussian.x_fwhm * gaussian.y_fwhm)))

    return stars_fitted, bad_pixels


def find_star_dao(img, xycoords=None):
    """
    Finds the position of a star spot in an image taken with the FLI camera

    :param image_path: path for the image to be centered (String)

    :return: center of the star or (-1, -1) if an error has occurred. (float, float)
    """

    mean, median, std = sigma_clipped_stats(img, sigma=3.0)

    daofind = DAOStarFinder(fwhm=config.Starfinder.FWHM, threshold=5. * std,
                            brightest=1, xycoords=xycoords)
    sources = daofind(img - median)

    if sources is None:
        x_star = np.nan
        y_star = np.nan
        peak = np.nan
        fwhm = np.nan

    else:
        x_star = sources[0]['xcentroid']
        y_star = sources[0]['ycentroid']
        peak = sources[0]['peak']

        if 50 < y_star < 1024 - 50 and 50 < y_star < 1024 - 50:
            fwhm = compute_fwhm(img, x_star, y_star)
        else:
            fwhm = np.nan

    return x_star, y_star, peak, fwhm


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


def find_star_custom_algo(image, spot_size=7, estim_error=0.05, nb_step=5,
                          laser_spot=False):
    """
    Finds the position of a star or laser lamp spot in an image taken with the FLI camera

    :param image_path: path for the image to be centered (String)
    :param spot_size: size of the spot for the search of the star in pixel. Must be odd. (int)
    :param estim_error: margin of error for the Gaussian fitting (float)
    :param nb_step: Precision settings (int)
    :param laser_spot: flag to disable PSF quality check for saturated laser lamp spot

    :return: center of the star or (-1, -1) if an error has occurred. (float, float)
    """

    tb = time.monotonic()

    # middle of the spot
    mid = int(spot_size / 2)

    # weighting matrix for score calcul
    w1, w2 = np.abs(np.mgrid[-mid:mid + 1, -mid:mid + 1])
    weighting = w1 + w2
    weighting[mid, mid] = 1

    # set the minimum brightness for a pixel to be considered in score calculation
    median = np.median(image)
    hist, bin_edges = np.histogram(image[~np.isnan(image)], bins=4096,
                                   range=(median - 10, median + 10))
    # Dividing lumino by two compared to original version of code.
    lumino = np.float32((hist * bin_edges[:-1]).sum() / hist.sum() * 10) / 2

    #if lumino < image.max():
    # TODO this quality check doesn't make much sense
    if not laser_spot and 3 * lumino < image.max():
        # Dirty hack in the black box...
        # Image quality insufficient for centering
        print(
            f'Image quality insufficient for centering {lumino} < {image.max()}'
        )
        return -1, -1

    # for each pixel, check if it's brighter than lumino, then check index limit
    # if all ok: divide spot around the pixel by the weighting matrix
    # after that, score is a matrix with luminosity score of all pixel brighter than lumino
    shape = image.shape
    score = np.zeros((shape[0], shape[1]))
    for i in range(shape[0]):
        for j in range(shape[1]):
            if image[i, j] > lumino:
                if i + mid + 1 <= shape[0] and j + mid + 1 <= shape[
                        1] and i - mid >= 0 and j - mid >= 0:
                    score[i, j] = np.divide(
                        image[i - mid:i + mid + 1, j - mid:j + mid + 1],
                        weighting).sum()

    # find the max of score matrix and get coordinate of it
    # argmax return flat index, unravel_index return right format
    (y, x) = np.unravel_index(np.argmax(score), score.shape)
    star_spot = image[y - mid:y + mid + 1, x - mid:x + mid + 1]

    # create x,y component for gaussian calculation.
    # corresponds to the coordinates of the picture
    y_gauss, x_gauss = np.mgrid[0:spot_size, 0:spot_size]
    #y_gauss, x_gauss = np.mgrid[y - mid:y + mid + 1, x - mid:x + mid + 1]

    if x_gauss.shape == star_spot.shape:
        x_mean = np.average(x_gauss, weights=star_spot)
        y_mean = np.average(y_gauss, weights=star_spot)
    else:
        print("Star not found. Human intervention needed!")
        return -1, -1

    # standard deviation of the spot selected
    # from g(x,y) = A * e^(− a(x−x_mean)² − b(x−x_mean)(y−y_mean) − c(y−y_mean)²)
    # with a = (cos²(θ)/2σ² + sin²(θ)/2σ²)
    #      b = (sin(2θ)/2σ² − sin(2θ)/2σ²)
    #      c = (sin²(θ)/2σ² + cos²(θ)/2σ²)
    # for  θ = 0, we got:
    #      a = 1/2σ²
    #      b = 0
    #      c = 1/2σ²
    # then σ = sqrt( ((x−x_mean)² - (y−y_mean)²) / (2 * ln(g(x,y)/A))
    # nomina = (x−x_mean)² - (y−y_mean)²
    # denomi = 2*ln(g(x,y)/A)
    nomina = -(np.power(y_gauss - mid, 2) + np.power(x_gauss - mid, 2))
    denomi = 2 * np.log(np.divide(star_spot, star_spot[mid, mid]))
    denomi[mid, mid] = 1
    result = np.divide(nomina, denomi)
    # the stdev of the middle is 0 by def, so we put NaN and use np.nanmean
    result[mid, mid] = np.nan
    sigma = np.nanmean(np.sqrt(np.abs(result)))

    mean = np.mean(star_spot)

    opti = 1
    x_f, y_f = 0, 0
    i_f = 0
    rng_step = 1
    ampl = image[y, x]

    # divide the area around the center (x_mean, y_mean) into nb_step * nb_step points
    # and find the point that minimizes the difference between the approximate gaussian and star_spot
    # Then repeat 3 times zooming in on the selected point
    # For each try, check with variation of sigma.
    for _ in range(3):
        for i in np.arange(-1, 1, 0.2):
            a_c = 0.5 / ((sigma + i)**2)

            for j in np.linspace(-rng_step / 2, rng_step / 2,
                                 nb_step*2 + 1)[1::2]:
                ydiff = (y_gauss - (y_mean+j))**2

                for k in np.linspace(-rng_step / 2, rng_step / 2,
                                     nb_step*2 + 1)[1::2]:
                    xdiff = (x_gauss - (x_mean+k))**2
                    gauss = ampl * np.exp(-((a_c*ydiff) + (a_c*xdiff)))
                    ratio = np.mean(np.abs(star_spot - gauss)) / mean

                    if opti > ratio:
                        opti = ratio
                        x_f, y_f = x_mean + k, y_mean + j
                        i_f = i

        x_mean = x_f
        y_mean = y_f
        rng_step /= nb_step

    tf = time.monotonic()
    print("time:", tf - tb)

    print("-----------------------")
    print("Window center :", (x_f, y_f))
    print("std    :", sigma + i_f)
    print("lum min:", lumino)
    print("ratio  :", opti)

    x_star = x + x_f - mid
    y_star = y + y_f - mid

    print("Center :", (x_star, y_star))
    print("-----------------------")

    if not laser_spot and opti > estim_error:
        print("That's not enough.. Human intervention needed !")
        return -1, -1

    return x_star, y_star


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


def compute_fwhm(image, xc, yc, psf_bb=50, bg_bb=20):
    """
    Compute the FWHM of a PSF by calculating the diamater of the area at half maximum.

    :param image: array containing the PSF
    :param xc: x position of the PSF center
    :param yc: y position of the PSF center
    :param psf_bb: window size to use for the psf fwhm
    :param bg_bb: window size to use for the corner background estimation
    :return:
    """

    xc = int(np.round(xc))
    yc = int(np.round(yc))

    # Take the median of every corners median
    background = np.median([
        np.median(image[0:bg_bb, 0:bg_bb]),
        np.median(image[0:bg_bb, -bg_bb:]),
        np.median(image[-bg_bb:, 0:bg_bb]),
        np.median(image[-bg_bb:, -bg_bb:])
    ])

    box = image[yc - psf_bb:yc + psf_bb, xc - psf_bb:xc + psf_bb] - background

    circle = (2 * box > box.max()).sum()
    if circle == 0:
        fwhm = -1
    else:
        fwhm = 2 * np.sqrt(circle / np.pi)

    return fwhm


def fit_2dgaussian(image, xc, yc, bb):
    """
    Fits a 2d gausssian model to the PSF.

    :param image: array containing the PSF
    :param xc: x position of the PSF center
    :param yc: y position of the PSF center
    :param bb: window size to use
    :return:
    """

    xc = int(np.round(xc))
    yc = int(np.round(yc))

    box = image[yc - bb:yc + bb, xc - bb:xc + bb]
    yp, xp = box.shape

    # Generate grid of same size like box to put the fit on
    y, x, = np.mgrid[:yp, :xp]
    # Declare what function you want to fit to your data
    f_init = models.Gaussian2D()
    # Declare what fitting function you want to use
    fit_f = fitting.LevMarLSQFitter()

    # Fit the model to your data (box)
    f = fit_f(f_init, x, y, box)

    return f


if __name__ == "__main__":
    import matplotlib.pyplot as plt

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

    frame = np.clip(np.rint(frame), 0, 2**16 - 1)

    start = time.monotonic()
    stars, bad_pixels = find_stars_and_bad_pixels(frame)
    print(time.monotonic() - start)

    frame_nan = frame.copy()
    frame_nan[bad_pixels] = np.nan

    plt.figure()
    plt.imshow(frame, norm='log', vmin=np.nanmin(frame_nan),
               vmax=np.nanmax(frame_nan))

    fig = plt.gcf()
    ax = fig.gca()

    for x, y, peak, fwhm in stars:
        plt.plot(x, y, 'r+')
        ax.add_patch(
            plt.Circle((x, y), fwhm / 2, edgecolor='r', facecolor='#ffffff00'))

    plt.plot(bad_pixels[:, 1], bad_pixels[:, 0], 'g+')

    plt.show()
