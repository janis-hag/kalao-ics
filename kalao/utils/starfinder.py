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

import time
from datetime import datetime

import numpy as np
import pandas as pd

from astropy import units as u
from astropy import wcs
from astropy.coordinates import AltAz, SkyCoord
from astropy.io import fits
from astropy.modeling import fitting, models
from astropy.stats import sigma_clipped_stats
from astropy.time import Time
from photutils.detection import DAOStarFinder

from kalao import euler, system
from kalao.cacao import aocontrol
from kalao.fli import camera
from kalao.plc import calib_unit, filterwheel, flip_mirror, laser, shutter
from kalao.utils import database, file_handling, kalao_time

from tcs_communication import t120

from kalao.definitions.enums import (FlipMirrorPosition, ReturnCode,
                                     SequencerStatus, ShutterState)
from kalao.definitions.exceptions import *
from kalao.definitions.exceptions import DMNotOn

import config


def center_on_target(kao='NO_AO', dit=config.FLI.exp_time):
    """
    Start star centering sequence:
    - Sets this filter based on filter_arg request.
    - Takes an image and search for the star position.
    - Send telescope offsets based on the measured position.
    - If auto centering does not work request manual centering

    :param dit:
    :param kao: flag to indicate if AO will be used, set to no by default.

    :return: 0 if centering succeded
    """

    timeout_time = time.monotonic(
    ) + config.Starfinder.centering_timeout + 3*dit

    # Check if we are alread on the star
    # if check_wfs_flux() == 0:
    #     # Start WFS centering procedure
    #     aocontrol.wfs_centering(
    #             tt_threshold=config.AO.WFS_centering_slope_threshold)
    #
    #     request_manual_centering(False)
    #
    #     return 0

    # Reset tip tilt stream to 0
    #aocontrol.reset_dm(config.AO.TTM_loop_number)

    while time.monotonic() < timeout_time:

        # Check if we are already on target
        if kao == 'AO':
            # Check if enough light is on the WFS for precise centering
            if aocontrol.optimize_wfs_flux() == 0:
                # if aocontrol.check_loops() != LoopStatus.ALL_LOOPS_ON:
                #     # Start WFS centering procedure
                #     aocontrol.wfs_centering(tt_threshold=config.AO.
                #                             WFS_centering_slope_threshold)
                #     aocontrol.tip_tilt_offload_ttm_to_telescope()

                return ReturnCode.CENTERING_OK

        # TODO use exptime given by nseq args
        image_path = camera.take_image(dit=dit)

        # TODO add dit optimisation
        #  focusing_dit = optimise_dit(focusing_dit)

        if image_path is None:
            system.print_and_log(f'ERROR no image received.')
            return -1

        x, y, peak, fwhm = find_star(image_path)

        if x != -1 and y != -1:

            send_pixel_offset(x, y)

            image_path = camera.take_image(dit=dit)
            if image_path is None:
                system.print_and_log(f'ERROR no image received.')
                return -1

            x, y, peak, fwhm = find_star(image_path)

            if x != -1 and y != -1:
                # Fine centering with TTM
                aocontrol.tip_tilt_offset_fli_to_ttm(x - config.FLI.center_x,
                                                     y - config.FLI.center_y)

            if kao == 'AO':
                # Check if enough light is on the WFS for precise centering
                if aocontrol.optimize_wfs_flux() == 0:
                    # Start WFS centering procedure
                    #aocontrol.wfs_centering(tt_threshold=config.AO.
                    #                        WFS_centering_slope_threshold)

                    request_manual_centering(False)

                    return ReturnCode.CENTERING_OK
                else:
                    # Retry centering
                    system.print_and_log(
                        'No light on WFS, re-centering with FLI')
                    continue

            else:
                # Centering is good enough
                request_manual_centering(False)
                return ReturnCode.CENTERING_OK

        else:
            # Start manual centering
            # TODO start timeout (value in kalao.config)
            # Set flag for manual centering
            request_manual_centering(True)

            # Wait 10 seconds before trying another star detection
            time.sleep(10)
            continue

            # if kao == 'AO':
            #     while time.monotonic() < timeout_time:
            #
            #         # Check if we are centered and exit loop
            #         ret = optimize_wfs_flux()
            #         if ret == 0:
            #             request_manual_centering(False)
            #             return 0

            #
            # else:
            #     # TODO for centering
            #     return 0

            # TODO wait for observer input
            # TODO send gop message
            # TODO send offset to telescope
            # TODO verify if SHWFS enough illuminated
            # if shwfs ok:
            #    return 0

    else:
        return ReturnCode.CENTERING_TIMEOUT


def center_on_laser():
    """
    Center the calibration unit the laser on the WFS.

    1. Move calibration unit close to correct position
    1. Close shutter
    2. Turn laser on
    3. Move flip mirror up
    4. Get laser offset
    5. Move calibration unit to new position

    :return:
    """

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    # Move calib unit to approximately correct position if too far #TODO: make similar to others
    if np.abs(calib_unit.plc_status()['lrPosActual'] -
              config.Laser.position) > 0.5:
        calib_unit.move_to_laser_position()

    if filterwheel.set_filter(
            config.FLI.laser_calib_filter) != config.FLI.laser_calib_filter:
        raise FilterWheelNotInPosition

    if shutter.close() != ShutterState.CLOSED:
        raise ShutterNotClosed

    if flip_mirror.up() != FlipMirrorPosition.UP:
        raise FlipMirrorNotUp

    laser.set_intensity(config.FLI.laser_calib_intensity)

    # Reset tip tilt stream to 0
    aocontrol.reset_dm(config.AO.TTM_loop_number)

    # Rough centering loop with FLI
    for i in range(3):
        print(f'Centering step {i}')

        image = camera.take_frame(dit=config.FLI.laser_calib_dit)

        # X can be changed by the ttm_tip_offset value
        # Y can be changed by the calib_unit position or ttm_tilt_offset value
        x, y = find_star_custom_algo(image, spot_size=7, estim_error=0.05,
                                     nb_step=5, laser_spot=True)

        if x != -1 and y != -1:
            calib_unit.move_px(config.FLI.center_y - y)
            time.sleep(3)

        # Check the new x position after the calib unit has been moved
        image = camera.take_frame(dit=config.FLI.laser_calib_dit)

        # X can be changed by the ttm_tip_offset value
        # Y can be changed by the calib_unit position or ttm_tilt_offset value
        x, y = find_star_custom_algo(image, spot_size=7, estim_error=0.05,
                                     nb_step=5, laser_spot=True)

        if x != -1 and y != -1:
            aocontrol.tip_tilt_offset_fli_to_ttm(x - config.FLI.center_x, 0)

    # Precise centering with WFS
    aocontrol.emgain_off()

    laser.set_intensity(config.WFS.laser_calib_intensity)
    aocontrol.set_exptime(config.WFS.laser_calib_exptime)

    aocontrol.tip_tilt_wfs_to_ttm()

    return 0


def request_manual_centering(flag=True):
    # TODO add docstring

    database.store('obs', {'tracking_manual_centering': flag})


def manual_centering(x, y, AO=False, sequencer_arguments=None):
    # TODO add docstring
    # TODO verify value validity before sending

    send_pixel_offset(x, y)
    image_path = camera.take_image(dit=config.FLI.exp_time,
                                   sequencer_arguments=sequencer_arguments)
    if image_path is None:
        ret = -1
    else:
        ret = 0

    if AO:
        ret = aocontrol.optimize_wfs_flux()

    return ret


def send_pixel_offset(x, y):
    """
    Send offsets to telescope converting the pixel offset into telescope alt/az offset.

    :param x: pixel offset along the x axis
    :param y: pixel offset along the y axis
    :return: success status
    """

    alt_offset = (x - config.FLI.center_x) * config.FLI.px_x_to_onsky
    az_offset = (y - config.FLI.center_y) * config.FLI.px_y_to_onsky

    t120.send_altaz_offset(alt_offset, az_offset)

    time.sleep(2)

    return 0


def find_star(image_path, df_output=False):
    """
    Finds the position of a star spot in an image taken with the FLI camera

    :param image_path: path for the image to be centered (String)

    :return: center of the star or (-1, -1) if an error has occurred. (float, float)
    """

    hdu_list = fits.open(image_path)
    hdu_list.info()
    image = hdu_list[0].data
    hdu_list.close()

    mean, median, std = sigma_clipped_stats(image, sigma=3.0)

    daofind = DAOStarFinder(fwhm=config.Starfinder.FWHM, threshold=5. * std,
                            brightest=1)
    sources = daofind(image - median)

    if sources is None:
        print("Star not found. Human intervention needed!")
        x_star = -1
        y_star = -1
        peak = -1
        fwhm = -1

    else:
        print(sources)
        x_star = sources[0]['xcentroid']
        y_star = sources[0]['ycentroid']
        peak = sources[0]['peak']

        if 50 < y_star < 1024 - 50 and 50 < y_star < 1024 - 50:
            fwhm = compute_fwhm(image, x_star, y_star)
            print(f'{fwhm}')
        else:
            fwhm = -1

        database.store(
            'obs', {
                'psf_file': image_path.split('/')[-1],
                'psf_x': x_star,
                'psf_y': y_star,
                'psf_peak': peak,
                'psf_fwhm': fwhm
            })

    if df_output:
        return sources.to_pandas()

    else:
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


def focus_sequence(focus_points=4, focusing_dit=config.Starfinder.focusing_dit,
                   sequencer_arguments=None):
    """
    Starts a sequence to find best telescope M2 focus position.

    TODO normalise flux by integration time and adapt focusing_dit in case of saturation
    TODO handle abort of sequence

    :param focus_points: number of points to take for in the sequence
    :param focusing_dit: integration time for each image
    :return:
    """

    if sequencer_arguments is None:
        q = None
    else:
        q = sequencer_arguments.get('q')

    # TODO define focusing_dit in kalao.config or pass as argument
    focus_points = np.around(focus_points)

    initial_focus = t120.get_focus_value()

    # focusing_dit = optimise_dit(focusing_dit)
    #
    # if focusing_dit == -1:
    #     system.print_and_log(
    #             'Error optimising dit for focusing sequence. Target brightness out of range'
    #     )

    file_path = camera.take_image(dit=focusing_dit,
                                  sequencer_arguments=sequencer_arguments)

    #time.sleep(5)
    file_handling.add_comment(file_path, 'Focus sequence: 0')

    image = fits.getdata(file_path)
    flux = np.sort(np.ravel(image))[-config.Starfinder.focusing_pixels:].sum()

    if flux < config.Starfinder.min_flux:
        database.store(
            'obs', {
                'sequencer_log': '[ERROR] No flux detected',
                'sequencer_status': SequencerStatus.ERROR
            })
        return -1

    focus_flux = pd.DataFrame({'set_focus': [initial_focus], 'flux': [flux]})

    # Get even number of focus_points in order to include 0 in the sequence.
    if (focus_points % 2) == 1:
        focus_points = focus_points + 1

    focusing_sequence = (np.arange(focus_points + 1) -
                         focus_points/2) * config.Starfinder.focusing_step

    for step, focus_offset in enumerate(focusing_sequence):
        database.store(
            'obs',
            {
                'sequencer_log': f'Focus {step+1}:{len(focusing_sequence)}',
                'sequencer_status':
                    f'Focus {step+1}:{len(focusing_sequence)}'  #TODO: this is irregular, do better
            })

        # Check if an abort was requested
        if q is not None and not q.empty():
            q.get()
            return -1
        if focus_offset == 0:
            # skip set_focus zero as it was already taken
            continue

        new_focus = focus_offset + initial_focus

        t120.send_focus_offset(new_focus)

        # TODO: Remove sleep if send_focus is blocking
        time.sleep(15)

        file_path = camera.take_image(dit=focusing_dit,
                                      sequencer_arguments=sequencer_arguments)

        file_handling.add_comment(file_path, f'Focus sequence: {new_focus}')

        image = fits.getdata(file_path)

        flux = np.sort(
            np.ravel(image))[-config.Starfinder.focusing_pixels:].sum()

        focus_flux.loc[len(focus_flux.index)] = [new_focus, flux]

    # Keep best set_focus
    best_focus = focus_flux.loc[focus_flux['flux'].idxmax(), 'set_focus']

    print(focus_flux)

    database.store('obs', {'sequencer_log': f'Best focus value: {best_focus}'})

    temps = t120.get_tube_temp()

    if (time.time() -
            float(temps.tunix)) < float(config.T120.temperature_file_timeout):

        database.store(
            'obs', {
                'focusing_best': best_focus,
                'focusing_temttb': temps.temttb,
                'focusing_temtth': temps.temtth,
                'focusing_fo_delta': best_focus - initial_focus
            })

    # best_focus = initial_focus + correction
    t120.update_fo_delta(best_focus - initial_focus)

    return 0


def get_latest_fo_delta():

    fo_delta_record = database.get_last('obs', 'focusing_fo_delta')

    if fo_delta_record == {}:
        return None

    fo_delta_age = (kalao_time.now() -
                    fo_delta_record['timestamp']).total_seconds()

    if fo_delta_age > 12 * 3600:
        return None
    else:
        return fo_delta_record['value']


def optimise_dit(starting_dit, sequencer_arguments=None,
                 min_flux=config.Starfinder.min_flux,
                 max_flux=config.Starfinder.max_flux):
    """
    Search for optimal dit value to reach the requested ADU.

    TODO implement filter change to nd if dit too short.

    :return: optimal dit value
    """

    new_dit = starting_dit

    for i in range(config.Starfinder.dit_optimization_trials):

        file_path = camera.take_image(dit=new_dit,
                                      sequencer_arguments=sequencer_arguments)

        #time.sleep(20)
        file_handling.add_comment(file_path,
                                  "Dit optimisation sequence: " + str(new_dit))

        image = fits.getdata(file_path)
        # flux = image[np.argpartition(image, -6)][-6:].sum()
        #flux = np.sort(np.ravel(image))[-focusing_pixels:].sum()

        print(new_dit, image.max(), max_flux, min_flux)
        if image.mean() >= max_flux:
            new_dit = int(np.floor(max_flux / (1.5 * image.mean())))
            #new_dit = int(np.floor(0.8 * new_dit))
            if new_dit <= 1:
                print('Max flux ' + str(image.max()) +
                      ' above max permitted value ' + str(max_flux))
                return -1
            continue
        elif image.mean() <= min_flux:
            new_dit = int(np.floor(1.5 * min_flux / image.mean()))
            #new_dit = int(np.ceil(1.2 * new_dit))
            if new_dit >= config.Starfinder.max_dit:
                print('Max flux ' + str(image.max()) +
                      ' below minimum permitted value: ' + str(min_flux))
                return -1
            continue
        else:
            break

    print('Optimal dit: ' + str(new_dit))

    return new_dit


def generate_night_darks(science_folder=None):
    """
    Generate the darks needed for the calibration of the night which is assumed to have ended.

    :param filepath:
    :return:
    """

    # TODO add docstring

    if science_folder is None:
        _, science_folder = file_handling.create_night_folders()

    exp_times = file_handling.get_exposure_times(science_folder)

    if len(exp_times) == 0:
        system.print_and_log(
            f'WARN: Not generating darks as {science_folder} is empty.')
        return 0
    else:
        for dit in exp_times:
            for i in range(10):
                print(dit, i)
                image_path = camera.take_dark(dit=dit)
                with fits.open(image_path, mode='update') as hdul:
                    hdul[0].header.set('HIERARCH ESO OBS TYPE', 'K_DARK')
                    hdul[0].header.set('HIERARCH ESO OBS TARGET NAME', 'Dark')
                    hdul.flush()

    return 0


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
    #w.wcs.crval = [c.ra.to_value(), c.dec.to_value()]
    coord = euler.telescope_coord()

    w.wcs.crval = [coord.ra.degree, coord.dec.degree]

    # Gnomonic (TAN) projection
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]

    return w


def calc_parang(dt=None, coord=None):
    location = euler.observing_location()

    if isinstance(dt, datetime):
        astro_time = Time(dt, scale='utc', location=location)
        print(f'Using custom date: {astro_time}')

    else:
        astro_time = Time(datetime.utcnow(), scale='utc', location=location)

    if isinstance(coord, SkyCoord):
        print(f'Using custom coord: {coord}')
    else:
        coord = euler.telescope_coord()

    r2d = 180 / np.pi
    d2r = np.pi / 180

    geolat_rad = config.Euler.latitude * d2r

    lst = astro_time.sidereal_time('mean').hour

    ha_deg = lst - coord.ra.value
    dec_deg = coord.dec.value

    # ha_deg=(float(hdr['LST'])*15./3600)-ra_deg

    # VLT TCS formula
    f1 = float(np.cos(geolat_rad) * np.sin(d2r * ha_deg))
    f2 = float(
        np.sin(geolat_rad) * np.cos(d2r * dec_deg) -
        np.cos(geolat_rad) * np.sin(d2r * dec_deg) * np.cos(d2r * ha_deg))
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
        fwhm = 2 * np.sqrt((2 * box > box.max()).sum() / np.pi)

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
