#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : calib_unit
# @Date : 2021-01-02-14-36
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
Utilities for star and laser centering.

starfinder.py is part of the KalAO Instrument Control Software (KalAO-ICS).
"""

import os
import sys
import time
from pathlib import Path
import pandas as pd

# add the necessary path to find the folder kalao for import
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from kalao.fli import camera
from kalao.plc import filterwheel, laser, shutter, flip_mirror, calib_unit
from kalao.utils import database, file_handling
from kalao.cacao import telemetry, aocontrol
from tcs_communication import t120
from sequencer import system

import numpy as np
from astropy.io import fits
from configparser import ConfigParser

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
parser = ConfigParser()
parser.read(config_path)
ExpTime = parser.getfloat('FLI', 'ExpTime')
CenterX = parser.getint('FLI', 'CenterX')
CenterY = parser.getint('FLI', 'CenterY')
PixScale = parser.getfloat('FLI', 'PixScale')
LaserCalibDIT = parser.getfloat('FLI', 'LaserCalibDIT')
LaserCalibIntensity = parser.getfloat('PLC', 'LaserCalibIntensity')

CenteringTimeout = parser.getfloat('Starfinder', 'CenteringTimeout')
FocusingStep = parser.getfloat('Starfinder', 'FocusingStep')
FocusingPixels = parser.getint('Starfinder', 'FocusingPixels')
FocusingDit = parser.getint('Starfinder', 'FocusingDit')
MinFlux = parser.getfloat('Starfinder', 'MinFlux')
MaxFlux = parser.getfloat('Starfinder', 'MaxFlux')
MaxDit = parser.getint('Starfinder', 'MaxDit')
DitOptimisationTrials = parser.getint('Starfinder', 'DitOptimisationTrials')

WFSilluminationThreshold = parser.getfloat('AO', 'WFSilluminationThreshold')
WFSilluminationFraction = parser.getfloat('AO', 'WFSilluminationFraction')
TTSlopeThreshold = parser.getfloat('AO', 'TTSlopeThreshold')


def centre_on_target(filter_arg='clear', kao='NO_AO'):
    """
    Start star centering sequence:
    - Sets this filter based on filter_arg request.
    - Takes an image and search for the star position.
    - Send telescope offsets based on the measured position.
    - If auto centering does not work request manual centering

    :param kao:
    :param filter_arg:
    :return: 0 if centering succeded
    """
    # Add loop timeout
    if filterwheel.set_position(filter_arg) == -1:
        system.print_and_log("Error: problem with filter selection")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    timeout_time = time.time() + CenteringTimeout

    while time.time() < timeout_time:
        # TODO use exptime given by nseq args
        rValue, image_path = camera.take_image(dit=ExpTime)

        # TODO add dit optimisation
        #  focusing_dit = optimise_dit(focusing_dit)

        # image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values'][0]
        # file_handling.save_tmp_image(image_path)

        if rValue != 0:
            # print(rValue)
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        x, y = find_star(image_path)

        if x != -1 and y != -1:

            send_pixel_offset(x, y)

            if kao == 'AO':
                if verify_centering() == 0:
                    request_manual_centering(False)

                    return 0
                else:
                    request_manual_centering(True)
            else:
                request_manual_centering(False)

                return 0

        else:
            # Start manual centering
            # TODO start timeout (value in kalao.config)
            # Set flag for manual centering
            request_manual_centering(True)

            if kao == 'AO':
                while time.time() < timeout_time:

                    # Check if we are centered and exit loop
                    rValue = verify_centering()
                    if rValue == 0:
                        request_manual_centering(False)
                        return 0

                    time.sleep(15)

            else:
                # TODO for centering
                return 0

            # TODO wait for observer input
            # TODO send gop message
            # TODO send offset to telescope
            # TODO verify if SHWFS enough illuminated
            # if shwfs ok:
            #    return 0

            pass


def center_on_laser():
    """
    Center the calibration unit the laser on the WFS.

    1. Close shutter
    2. Turn laser on
    3. Move flip mirror up
    4. Get laser offset
    5. Move calibration unit to new position

    :return:
    """

    if filterwheel.set_position('ND') == -1:
        system.print_and_log("Error: problem with filter selection")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if shutter.shutter_close() != 'CLOSED':
        system.print_and_log("Error: failed to close the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    #
    laser.set_intensity(LaserCalibIntensity)

    if flip_mirror.up() != 'UP':
        system.print_and_log("Error: flip mirror did not go up")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    rValue, image_path = camera.take_image(dit=LaserCalibDIT)

    # X can be changed by the ttm_tip_offset value
    # Y can be changed by the calib_unit position or ttm_tilt_offset value
    x, y = find_star(image_path, spot_size=7, estim_error=0.05, nb_step=5,
                     laser=True)

    if x != -1 and y != -1:
        calib_unit.pixel_move(y)

    return 0


def request_manual_centering(flag=True):
    database.store_obs_log({'tracking_manual_centering': flag})


def manual_centering(x, y):

    # TODO verify value validity before sending

    send_pixel_offset(x, y)
    rValue, image_path = camera.take_image(dit=ExpTime)
    rValue = verify_centering()

    return rValue


def send_pixel_offset(x, y):
    """
    Send offsets to telescope converting the pixel offset into telescope alt/az offset.

    :param x: pixel offset along the x axis
    :param y: pixel offset along the y axis
    :return: success status
    """
    # Found star
    alt_offset = (x - CenterX) * PixScale
    az_offset = (y - CenterY) * PixScale

    # TODO transform pixel x y into arcseconds
    # TODO uncomment when gui testing finished
    t120.send_offset(alt_offset, az_offset)

    system.print_and_log(f'Sending offset: {alt_offset=} {az_offset=}')

    time.sleep(2)

    return 0


def verify_centering():
    # TODO verify if SHWFS is enough illuminated
    illuminated_fraction = telemetry.wfs_illumination_fraction(
            WFSilluminationThreshold)

    aocontrol.wfs_centering(TTSlopeThreshold)

    if illuminated_fraction > WFSilluminationFraction:
        system.print_and_log('WFS on target')
        return 0


def find_star(image_path, spot_size=7, estim_error=0.05, nb_step=5,
              laser=False):
    """
    Finds the position of a star or laser lamp spot in an image.

    :param image_path: path for the image to be centered (String)
    :param spot_size: size of the spot for the search of the star in pixel. Must be odd. (int)
    :param estim_error: margin of error for the Gaussian fitting (float)
    :param nb_step: Precision settings (int)
    :param laser: flag to disable PSF quality check for saturated laser lamp spot

    :return: center of the star or (-1, -1) if an error has occurred. (float, float)
    """

    tb = time.time()
    hdu_list = fits.open(image_path)
    hdu_list.info()
    image = hdu_list[0].data
    hdu_list.close()

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
    if not laser and 3 * lumino < image.max():
        # Dirty hack in the black box...
        # Image quality insufficient for centering
        system.print_and_log(
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
        print("Star not found.. Human intervention needed !")
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
                                 nb_step * 2 + 1)[1::2]:
                ydiff = (y_gauss - (y_mean + j))**2

                for k in np.linspace(-rng_step / 2, rng_step / 2,
                                     nb_step * 2 + 1)[1::2]:
                    xdiff = (x_gauss - (x_mean + k))**2
                    gauss = ampl * np.exp(-((a_c * ydiff) + (a_c * xdiff)))
                    ratio = np.mean(np.abs(star_spot - gauss)) / mean

                    if opti > ratio:
                        opti = ratio
                        x_f, y_f = x_mean + k, y_mean + j
                        i_f = i

        x_mean = x_f
        y_mean = y_f
        rng_step /= nb_step

    tf = time.time()
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

    if not laser and opti > estim_error:
        print("That's not enough.. Human intervention needed !")
        return -1, -1

    return x_star, y_star


def focus_sequence(focus_points=6, focusing_dit=FocusingDit):
    """
    Starts a sequence to find best telescope M2 focus position.

    TODO normalise flux by integration time and adapt focusing_dit in case of saturation

    :param focus_points: number of points to take for in the sequence
    :param focusing_dit: integration time for each image
    :return:
    """
    # TODO define focusing_dit in kalao.config or pass as argument
    focus_points = np.around(focus_points)

    initial_focus = t120.get_focus_value()

    focusing_dit = optimise_dit(focusing_dit)

    if focusing_dit == -1:
        system.print_and_log(
                'Error optimising dit for focusing sequence. Target brightness out of range'
        )

    req, file_path = camera.take_image(dit=focusing_dit)

    #time.sleep(5)
    file_handling.add_comment(file_path, "Focus sequence: 0")

    image = fits.getdata(file_path)
    flux = np.sort(np.ravel(image))[-FocusingPixels:].sum()

    focus_flux = pd.DataFrame({'set_focus': [initial_focus], 'flux': [flux]})

    # Get even number of focus_points in order to include 0 in the sequence.
    if (focus_points % 2) == 1:
        focus_points = focus_points + 1

    focusing_sequence = (np.arange(focus_points + 1) -
                         focus_points / 2) * FocusingStep

    for step, focus_offset in enumerate(focusing_sequence):
        system.print_and_log(f'Focus step: {step+1}/{len(focusing_sequence)}')

        if focus_offset == 0:
            # skip set_focus zero as it was already taken
            continue

        new_focus = focus_offset + initial_focus

        t120.send_focus_offset(new_focus)

        # Remove sleep if send_focus is blocking
        time.sleep(15)

        req, file_path = camera.take_image(dit=focusing_dit)

        #time.sleep(20)
        file_handling.add_comment(file_path,
                                  "Focus sequence: " + str(new_focus))

        image = fits.getdata(file_path)
        # flux = image[np.argpartition(image, -6)][-6:].sum()
        flux = np.sort(np.ravel(image))[-FocusingPixels:].sum()

        focus_flux.loc[len(focus_flux.index)] = [new_focus, flux]

    # Keep best set_focus
    best_focus = focus_flux.loc[focus_flux['flux'].idxmax(), 'set_focus']

    print(focus_flux)

    system.print_and_log('best focus value: ' + str(best_focus))
    database.store_obs_log({'tracking_log': best_focus})

    t120.send_focus_offset(best_focus)

    return 0


def optimise_dit(focusing_dit):
    """
    Search for optimal dit value to reach the requested ADU.

    TODO implement filter change to nd if dit too short.

    :return: optimal dit value
    """

    new_dit = focusing_dit

    for i in range(DitOptimisationTrials):

        req, file_path = camera.take_image(dit=new_dit)

        #time.sleep(20)
        file_handling.add_comment(file_path,
                                  "Dit optimisation sequence: " + str(new_dit))

        image = fits.getdata(file_path)
        # flux = image[np.argpartition(image, -6)][-6:].sum()
        #flux = np.sort(np.ravel(image))[-FocusingPixels:].sum()

        print(new_dit, image.max(), MaxFlux, MinFlux)
        if image.max() >= MaxFlux:
            new_dit = int(np.floor(0.8 * new_dit))
            if new_dit <= 1:
                print('Max flux ' + str(image.max()) +
                      ' above max permitted value ' + str(MaxFlux))
                return -1
            continue
        elif image.max() <= MinFlux:
            new_dit = int(np.ceil(1.2 * new_dit))
            if new_dit >= MaxDit:
                print('Max flux ' + str(image.max()) +
                      ' below minimum permitted value: ' + str(MinFlux))
                return -1
            continue
        else:
            break

    print('Optimal dit: ' + str(new_dit))

    return new_dit
