#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : open_loop_ncpa.py
# @Date : 2022-03-19-15-33
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
open_loop_ncpa.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path
from signal import SIGINT, signal
from sys import exit

import numpy as np

from astropy.io import fits

from kalao.cacao import aocontrol, toolbox
from kalao.fli import camera
from kalao.plc import filterwheel, laser
from kalao.utils import kmath, starfinder, zernike

from kalao.definitions.enums import CameraServerStatus

import config

PEAK_VALUE = 0
COEFF = 1

from kalao.utils.terminal_colors import TerminalColors as TC


def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected. Exiting.')
    ret = toolbox.zero_stream(config.Streams.DM_NCPA)

    if ret == 0:
        print('Resetted DM pattern')

    exit(0)


def take_and_measure(args):
    hw = args.roi_size // 2

    img_cube = camera.take_frame(
        exptime=args.exptime, nbframes=args.img_avg,
        roi=(config.FLI.center_x - hw, config.FLI.center_y - hw, 2 * hw,
             2 * hw))

    img = np.mean(img_cube, axis=0)

    star = starfinder.find_star(img)

    return star.peak


def display_and_measure(dm_stream, zernike_coeffs, args):
    pattern = zernike.generate_pattern(zernike_coeffs, dm_stream.shape)
    dm_stream.set_data(pattern, True)
    time.sleep(0.1)

    return take_and_measure(args)


def run(args):
    # Open DM stream
    dm_stream = toolbox.open_stream_once(config.Streams.DM_NCPA)
    if dm_stream is None:
        print(f'{config.Streams.DM_NCPA} missing')
        exit()

    # Open slopes stream
    slopes_stream = toolbox.open_stream_once(config.Streams.SLOPES)
    if slopes_stream is None:
        print(f'{config.Streams.SLOPES} missing')
        exit()

    toolbox.zero_stream(config.Streams.DM_NCPA)

    peak = take_and_measure(args)
    print(f'Exposure time: {args.exptime}')
    print(f'Initial peak: {peak}')

    zernike_coeffs = np.zeros(args.orders_to_correct)
    start_coeff = 0
    start_peak = peak
    end_coeff = np.nan
    end_peak = np.nan
    highest_peak = peak

    print('=========================================')
    print(
        f'Correcting {args.orders_to_correct} orders with {args.orders_to_skip} first orders skipped'
    )
    print()
    print(f'Current coefficients:')

    for i in range(args.iterations):
        for order in range(args.orders_to_skip, args.orders_to_correct):
            zernike.print_coeffs(zernike_coeffs)
            print(TC.CLEAR)

            print(TC.CLEAR + f'Highest peak recorded: {highest_peak:.1f}')
            print(TC.CLEAR)

            print(
                TC.CLEAR +
                f'Result of previous optimization: Zernike amplitude {start_coeff:f} -> {end_coeff:f}     Peak {start_peak:.1f} -> {end_peak:.1f}'
            )
            print(TC.CLEAR)

            coeff_name, (coeff_n, coeff_m) = zernike.get_coeff_name(order)

            print(
                TC.CLEAR +
                f'Iteration {i + 1}/{args.iterations}   Optimising order ({coeff_n: 2},{coeff_m: 2}) {coeff_name}'
            )

            n, m = zernike.Zernike.standard_inverse(order)
            norm = zernike.Zernike.N(n, m, norm='RMS')

            step = 0
            zernike_coeff_incr = 0.1 * 1.75 / norm  # DM range is between -1.75 and 1.75
            peak_array = np.zeros((3, 2))

            start_peak = peak_array[1][PEAK_VALUE] = display_and_measure(
                dm_stream, zernike_coeffs, args)
            start_coeff = peak_array[1][COEFF] = zernike_coeffs[order]

            # Reset value to zero before starting search
            zernike_coeffs[order] = 0

            print(
                TC.CLEAR +
                f'Starting point                          Zernike amplitude {peak_array[1][COEFF]: 11.8f}     Peak: {peak_array[1][PEAK_VALUE]:.0f}'
            )
            print(TC.CLEAR)

            while step < args.steps and zernike_coeff_incr > args.min_incr:
                up = zernike_coeffs[order] + zernike_coeff_incr
                down = zernike_coeffs[order] - zernike_coeff_incr

                # Test up
                zernike_coeffs[order] = up

                peak_array[2][PEAK_VALUE] = display_and_measure(
                    dm_stream, zernike_coeffs, args)
                peak_array[2][COEFF] = up

                # Test down
                zernike_coeffs[order] = down

                peak_array[0][PEAK_VALUE] = display_and_measure(
                    dm_stream, zernike_coeffs, args)
                peak_array[0][COEFF] = down

                # Get zernike value of max flux
                zernike_coeffs[order] = peak_array[
                    peak_array[:, PEAK_VALUE].argmax(), COEFF]

                # Set new value of center
                peak_array[1][PEAK_VALUE] = peak_array[:, PEAK_VALUE].max()
                peak_array[1][COEFF] = zernike_coeffs[order]

                print(
                    TC.UP + TC.CLEAR +
                    f'Step {step: 5d}     Increment {zernike_coeff_incr:.8f}     Zernike amplitude {peak_array[1][COEFF]: 11.8f}     Peak: {peak_array[1][PEAK_VALUE]:.0f}'
                )

                step += 1
                zernike_coeff_incr = zernike_coeff_incr / 2

            end_peak = peak_array[1][PEAK_VALUE] = display_and_measure(
                dm_stream, zernike_coeffs, args)
            end_coeff = peak_array[1][COEFF] = zernike_coeffs[order]

            highest_peak = max(highest_peak, end_peak)

            print(TC.UP * (8 + len(zernike_coeffs)), end=TC.CLEAR)

    peak = display_and_measure(dm_stream, zernike_coeffs, args)

    print(TC.UP + TC.CLEAR + f'Final coefficients:')
    zernike.print_coeffs(zernike_coeffs)
    print(TC.CLEAR)

    print(TC.CLEAR + f'Highest peak recorded: {highest_peak:.1f}')
    print(TC.CLEAR)

    print(TC.CLEAR + f'Final peak value: {peak:.1f}')
    print(TC.CLEAR)
    print(TC.CLEAR)
    print(TC.CLEAR)

    laser.set_power(config.WFS.laser_calib_power, enable=True)
    aocontrol.set_exptime(config.WFS.laser_calib_exptime)
    aocontrol.set_emgain(config.WFS.laser_calib_emgain)

    time.sleep(10)

    folder = Path(
        f'ncpa_{datetime.now(timezone.utc).isoformat(timespec="milliseconds")}'
    )
    folder.mkdir(parents=True)

    np.savetxt(folder / 'dm_zernike_coeffs.txt', zernike_coeffs)
    toolbox.save_stream_to_fits(config.Streams.DM, f'{folder}/dm.fits')

    print(f'Averaging slopes')
    slopes = []

    for i in range(args.slopes_avg):
        time.sleep(0.01)
        print(TC.UP + TC.CLEAR + f'Averaging slopes {i+1}/{args.slopes_avg}')
        slopes.append(slopes_stream.get_data(True))

    slopes = np.array(slopes)
    fits.PrimaryHDU(slopes).writeto(folder / 'slopes_cube.fits')

    slopes = np.median(slopes, axis=0)
    fits.PrimaryHDU(slopes).writeto(folder / 'slopes_median.fits')

    print(f'Results written')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run open-loop NCPA optimisation.')
    parser.add_argument('--exptime', action='store', dest='exptime',
                        type=float, default=config.FLI.laser_calib_exptime,
                        help='Science camera integration time')
    parser.add_argument('--filter', action='store', dest='filter_name',
                        default=config.FLI.laser_calib_filter,
                        help='Filter name to use')
    parser.add_argument('--laser', action='store', dest='laser_power',
                        default=config.FLI.laser_calib_power, type=float,
                        help='Laser power')
    parser.add_argument('--orders', action='store', dest='orders_to_correct',
                        default=10, type=int,
                        help='Number of orders to correct (including skipped)')
    parser.add_argument('--skip-orders', action='store', dest='orders_to_skip',
                        default=3, type=int, help='Number of orders to skip')
    parser.add_argument('--iterations', action='store', dest='iterations',
                        default=10, type=int, help='Number of iterations')
    parser.add_argument('--min_incr', action='store', dest='min_incr',
                        default=0.001, type=float,
                        help='Minimum increment for convergence')
    parser.add_argument('--steps', action='store', dest='steps', default=25,
                        type=int,
                        help='Maximum number of steps for convergence')
    parser.add_argument('--img_avg', action='store', dest='img_avg', default=5,
                        type=int, help='Averaging over images')
    parser.add_argument('--roi', action='store', dest='roi_size', default=40,
                        type=int, help='ROI size')
    parser.add_argument('--slopes_avg', action='store', dest='slopes_avg',
                        default=1000, type=int,
                        help='Number of frames to average slopes on')

    args = parser.parse_args()

    if not kmath.is_triangular(args.orders_to_correct):
        print(
            'Warning, the number of orders to correct is not triangular. Correction will be asymmetric.'
        )
        print(
            f'Recommended values are {", ".join(str(_) for _ in kmath.triangular_up_to(121))}'
        )

    if not kmath.is_triangular(args.orders_to_skip):
        print(
            'Warning, the number of orders to skip is not triangular. Correction will be asymmetric.'
        )
        print(
            f'Recommended values are {", ".join(str(_) for _ in kmath.triangular_up_to(121))}'
        )

    if camera.check_server_status() != CameraServerStatus.UP:
        print(
            'Error connecting to camera. Please try to restart the kalao_fli service.'
        )
        exit(-1)

    laser.set_power(args.laser_power, enable=True)

    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, handler)

    if filterwheel.set_filter(args.filter_name) != args.filter_name:
        print('Error with filter selection')

    run(args)
