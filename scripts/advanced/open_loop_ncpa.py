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
import sys

from time import sleep
from signal import signal, SIGINT
from sys import exit
import numpy as np
import pandas as pd

from kalao.cacao.aocontrol import check_stream
from kalao.cacao.toolbox import save_stream_to_fits, zero_stream
from kalao.utils import kalao_time, zernike
from kalao.plc import laser, filterwheel
from kalao.fli import camera

from pyMilk.interfacing.isio_shmlib import SHM

import kalao_config as config

PEAK_VALUE = 0
COEFF = 1


def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected. Exiting.')
    ret = zero_stream(r"dm01disp08")

    if ret == 0:
        print('Resetted DM pattern')

    exit(0)


def generate_pattern(R, Theta, zernike_coeffs):

    pattern = np.zeros(R.shape)

    for i, coeff in enumerate(zernike_coeffs):
        n, m = zernike.Zernike.standard_inverse(i + 3)
        pattern += coeff * zernike.Zernike.Z(n, m, R, Theta)

    return pattern


def run(args):
    dit = args.dit
    orders_to_correct = args.orders_to_correct
    steps = args.steps
    iterations = args.iterations
    max_flux = args.max_flux
    min_flux = args.min_flux
    max_dit = args.max_dit
    filter_name = args.filter_name
    min_incr = args.min_incr
    center = args.center
    window = args.window_size

    new_dit = dit

    # Search optimal dit
    while (True):
        img, _ = camera.take_frame(dit, do_not_log=True, cut_window=window,
                                   cut_center=center)

        print(new_dit, img.max())
        if img.max() >= max_flux:
            new_dit = 0.8 * new_dit
            if new_dit <= 1:
                print(f'Max flux {img.max()} above max permitted value {max_flux}'
                      )
                sys.exit(1)
            continue
        elif img.max() <= min_flux:
            new_dit = 1.2 * new_dit
            if new_dit >= max_dit:
                print(f'Max flux {img.max()} below minimum permitted value {min_flux}'
                      )
                sys.exit(1)
            continue
        else:
            break

    print(f'Setting DIT to {new_dit}')
    img, _ = camera.take_frame(dit, do_not_log=True, cut_window=window,
                               cut_center=center)

    # Open DM stream
    dm_stream_exists, dm_stream_path = check_stream("dm01disp08")
    if not dm_stream_exists:
        print(f'{dm_stream_path} stream missing')
        exit()

    dm_stream = SHM(dm_stream_path)

    x = np.linspace(-1, 1, dm_stream.shape[0])
    y = np.linspace(-1, 1, dm_stream.shape[1])

    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + y**2)
    Theta = np.arctan2(Y, X)

    zernike_coeffs = np.zeros(orders_to_correct)
    print(f'Correcting {orders_to_correct} orders')

    df = pd.DataFrame(columns=['peak_flux', 'iteration', 'order', 'step'] +
                      np.arange(len(zernike_coeffs)).tolist())

    for i in range(iterations):
        print('=========================================')
        print(f'Iteration {i + 1}/{iterations}')

        for order in range(0, orders_to_correct):
            print(f'Iteration {i + 1}/{iterations}   Optimising order {order + 3}'
                  )

            zernike_coeff_incr = 0.9 * 1.75 / 2  # DM range is between -1.75 and 1.75

            # Reset value to zero before starting search
            zernike_coeffs[order] = 0

            img, _ = camera.take_frame(dit, do_not_log=True, cut_window=window,
                                       cut_center=center)

            peak_array = np.zeros((3, 2))

            peak_array[1][PEAK_VALUE] = img.max()
            peak_array[1][COEFF] = zernike_coeffs[order]

            step = 0
            while step < steps and zernike_coeff_incr > min_incr:
                print(f'Step {step}     Increment {zernike_coeff_incr:.8f}     Zernike amplitude {zernike_coeffs[order]:.8f}     Max flux: {img.max():.0f}'
                      )

                up = zernike_coeffs[order] + zernike_coeff_incr
                down = zernike_coeffs[order] - zernike_coeff_incr

                # Test up
                zernike_coeffs[order] = up

                dm_stream.set_data(generate_pattern(R, Theta, zernike_coeffs),
                                   True)
                sleep(0.1)
                img, _ = camera.take_frame(dit, do_not_log=True,
                                           cut_window=window,
                                           cut_center=center,
                                           update_stream=False)

                peak_array[2][PEAK_VALUE] = img.max()
                peak_array[2][COEFF] = up

                # Test down
                zernike_coeffs[order] = down

                dm_stream.set_data(generate_pattern(R, Theta, zernike_coeffs),
                                   True)
                sleep(0.1)
                img, _ = camera.take_frame(dit, do_not_log=True,
                                           cut_window=window,
                                           cut_center=center,
                                           update_stream=False)

                peak_array[0][PEAK_VALUE] = img.max()
                peak_array[0][COEFF] = down

                # Get zernike value of max flux
                zernike_coeffs[order] = peak_array[
                        peak_array[:, PEAK_VALUE].argmax(), COEFF]

                df = df.append(
                        pd.Series(
                                np.concatenate((np.array([
                                        peak_array.max(), i, order, step
                                ]), zernike_coeffs)), index=df.columns),
                        ignore_index=True)

                # Set new value of center
                peak_array[1][PEAK_VALUE] = peak_array[:, PEAK_VALUE].max()
                peak_array[1][COEFF] = zernike_coeffs[order]

                step += 1
                zernike_coeff_incr = zernike_coeff_incr / 2

            print(zernike_coeffs)

    time_name = kalao_time.get_isotime()

    df.to_pickle(f'ncpa_scan_{time_name}.pickle')

    max_row = df.iloc[df.peak_flux.idxmax()]

    print(max_row)

    zernike_coeffs = max_row[-len(zernike_coeffs):].to_numpy()

    dm_stream.set_data(generate_pattern(R, Theta, zernike_coeffs), True)
    sleep(0.1)
    img, _ = camera.take_frame(dit, do_not_log=True, cut_window=window,
                               cut_center=center)

    # TODO update zp0 stream
    save_stream_to_fits('dm01disp', 'dmflat_ncpa_time_name.fits')
    save_stream_to_fits('shwfs_slopes', 'slopes_ncpa_time_name.fits')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Run open-loop NCPA optimisation.')
    parser.add_argument('-d', action="store", dest="dit", type=float,
                        default=config.FLI.laser_calib_dit,
                        help="Science camera integration time")
    parser.add_argument('-o', action="store", dest="orders_to_correct",
                        default=10, type=int,
                        help='Numbers of orders to correct')
    parser.add_argument('-s', action="store", dest="steps", default=25,
                        type=int, help='Number of steps')
    parser.add_argument('-i', action="store", dest="iterations", default=10,
                        type=int, help='Number of iterations')
    parser.add_argument('-max', action="store", dest="max_flux", default=2**15,
                        type=float, help='Maximum flux to have on the FLI')
    parser.add_argument('-min_flux', action="store", dest="min_flux",
                        default=2**11, type=int,
                        help='Minimum flux to have on the FLI')
    parser.add_argument('-max_dit', action="store", dest="max_dit",
                        default=0.5, type=float, help='Maximum dit of the FLI')
    parser.add_argument('-filter', action="store", dest="filter_name",
                        default='nd', help='Filter name to use')
    parser.add_argument('-min_incr', action="store", dest="min_incr",
                        default=0.0001, type=float,
                        help='Minimum increment for convergence')
    parser.add_argument('-c', action="store", dest="center",
                        default=[512, 512], nargs='+', type=int,
                        help='x y position of the window center')
    parser.add_argument('-w', action="store", dest="window_size", default=100,
                        type=int, help='Size of the window to cut out. ')
    parser.add_argument('-l', action="store", dest="laser_int",
                        default=config.Laser.calib_intensity, type=float,
                        help='Laser intensity.')

    args = parser.parse_args()
    dit = args.dit
    # orders_to_correct = args.orders_to_correct
    # steps = args.steps
    # iterations = args.iterations
    # max_flux = args.max_flux
    # min_flux = args.min_flux
    # max_dit = args.max_dit
    filter_name = args.filter_name
    # min_incr = args.min_incr
    # center = args.center
    # window = args.window_size
    laser_int = args.laser_int

    laser.set_intensity(laser_int)

    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, handler)

    if filterwheel.set_position(filter_name) == -1:
        print("Error with filter selection")
    sleep(2)

    run(args)
