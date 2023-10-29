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

from scipy import optimize

from kalao.cacao.aocontrol import check_stream, reset_dm
from kalao.cacao.toolbox import save_stream_to_fits, zero_stream
from kalao.utils import kalao_time, zernike
from kalao.plc import laser, filterwheel
from kalao.fli import camera

from pyMilk.interfacing.isio_shmlib import SHM

from kalao_enums import CameraServerStatus
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


def generate_pattern(zernike_coeffs, R, Theta):

    pattern = np.zeros(R.shape)

    for i, coeff in enumerate(zernike_coeffs):
        n, m = zernike.Zernike.standard_inverse(i + 3)
        pattern += coeff * zernike.Zernike.Z(n, m, R, Theta)

    return pattern

# yapf: disable
def gaussian_2d_rotated(x, y, mu_x = 0, mu_y = 0, sigma_x = 1, sigma_y = 1, theta = 0, A = None, C = 0):
    if A is None:
        A = 1/(sigma_x * sigma_y * 2*np.pi)

    a = np.cos(theta)**2/(2 * sigma_x**2) + np.sin(theta)**2/(2 * sigma_y**2)
    b = -np.sin(2*theta)/(4 * sigma_x**2) + np.sin(2*theta)/(4 * sigma_y**2)
    c = np.sin(theta)**2/(2 * sigma_x**2) + np.cos(theta)**2/(2 * sigma_y**2)

    return A * np.exp(-(a*(x - mu_x)**2 + 2*b*(x - mu_x)*(y - mu_y) + c*(y - mu_y)**2)) + C
# yapf: enable

def take_and_measure(update_stream=False):
    peak_hw = (args.peak_window-1) // 2

    max = 0
    x, y = np.mgrid[0:args.peak_window, 0:args.peak_window]

    for i in range(args.img_avg):
        img, _ = camera.take_frame(args.dit, do_not_log=True,
                                   update_stream=update_stream)

        peak_pos = np.unravel_index(np.argmax(img, axis=None), img.shape)

        img_peak = img[peak_pos[0] - peak_hw:peak_pos[0] + peak_hw + 1, peak_pos[1] -
                       peak_hw:peak_pos[1] + peak_hw + 1]

        p0 = (peak_hw, peak_hw, 2, 2, 0, img_peak[peak_hw, peak_hw])
        errorfunction = lambda p: np.ravel(
                gaussian_2d_rotated(x, y, *p) - img_peak)
        p, success = optimize.leastsq(errorfunction, p0)

        #print(f'mu_x: {p[0]}, mu_y: {p[1]}, sigma_x: {p[2]}, sigma_y: {p[3]}, theta: {p[4]}, A: {p[5]}, peak: {img_peak[peak_hw,peak_hw]}'
        #      )
        max += p[5]

    return max / args.img_avg


def display_and_measure(dm_stream, zernike_coeffs, R, Theta, args,
                     update_stream=False):
    dm_stream.set_data(generate_pattern(zernike_coeffs, R, Theta), True)
    sleep(0.1)

    return take_and_measure(update_stream)



def run(args):
    dit = args.dit
    orders_to_correct = args.orders_to_correct
    steps = args.steps
    iterations = args.iterations
    max_flux = args.max_flux
    min_flux = args.min_flux
    max_dit = args.max_dit
    min_incr = args.min_incr

    new_dit = dit

    reset_dm(1)

    # Search optimal dit
    while True:
        peak = take_and_measure()

        print(new_dit, peak)
        if peak >= max_flux:
            new_dit = 0.8 * new_dit
            if new_dit <= 1e-3:
                print(f'Max flux {img.max()} above max permitted value {max_flux}'
                      )
                sys.exit(1)
            continue
        elif peak <= min_flux:
            new_dit = 1.2 * new_dit
            if new_dit >= max_dit:
                print(f'Max flux {img.max()} below minimum permitted value {min_flux}'
                      )
                sys.exit(1)
            continue
        else:
            break

    print(f'Setting DIT to {args.dit}')

    # Open DM stream
    dm_stream_exists, dm_stream_path = check_stream("dm01disp08")
    if not dm_stream_exists:
        print(f'{dm_stream_path} stream missing')
        exit()

    dm_stream = SHM(dm_stream_path)

    x = np.linspace(-1, 1, dm_stream.shape[0])
    y = np.linspace(-1, 1, dm_stream.shape[1])

    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)

    zernike_coeffs = np.zeros(args.orders_to_correct)
    print(f'Correcting {args.orders_to_correct} orders with {args.orders_to_skip} first orders skipped')

    df = pd.DataFrame(columns=['peak_flux', 'iteration', 'order', 'step'] +
                      np.arange(len(zernike_coeffs)).tolist())

    for i in range(iterations):
        print('=========================================')
        print(f'Iteration {i + 1}/{iterations}')

        for order in range(args.orders_to_skip, args.orders_to_correct):
            print(f'Iteration {i + 1}/{iterations}   Optimising order {order}'
                  )

            step = 0
            zernike_coeff_incr = 0.9 * 1.75 / 2  # DM range is between -1.75 and 1.75
            peak_array = np.zeros((3, 2))

            # Reset value to zero before starting search
            zernike_coeffs[order] = 0

            peak_array[1][PEAK_VALUE] = display_and_measure(
                    dm_stream, zernike_coeffs, R, Theta, args)
            peak_array[1][COEFF] = zernike_coeffs[order]

            print(f'Step START     Increment       None     Zernike amplitude {peak_array[1][COEFF]: 11.8f}     Max flux: {peak_array[1][PEAK_VALUE]:.0f}'
                  )
            print(zernike_coeffs)

            while step < steps and zernike_coeff_incr > min_incr:
                up = zernike_coeffs[order] + zernike_coeff_incr
                down = zernike_coeffs[order] - zernike_coeff_incr

                # Test up
                zernike_coeffs[order] = up

                peak_array[2][PEAK_VALUE] = display_and_measure(
                        dm_stream, zernike_coeffs, R, Theta, args)
                peak_array[2][COEFF] = up

                # Test down
                zernike_coeffs[order] = down

                peak_array[0][PEAK_VALUE] = display_and_measure(
                        dm_stream, zernike_coeffs, R, Theta, args)
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

                print(f'Step {step: 5d}     Increment {zernike_coeff_incr:.8f}     Zernike amplitude {peak_array[1][COEFF]: 11.8f}     Max flux: {peak_array[1][PEAK_VALUE]:.0f}'
                      )

                step += 1
                zernike_coeff_incr = zernike_coeff_incr / 2

            peak_array[1][PEAK_VALUE] = display_and_measure(
                    dm_stream, zernike_coeffs, R, Theta, args,
                    update_stream=True)
            peak_array[1][COEFF] = zernike_coeffs[order]
            print(f'Step RESUL     Increment       None     Zernike amplitude {peak_array[1][COEFF]: 11.8f}     Max flux: {peak_array[1][PEAK_VALUE]:.0f}'
                  )
            print(zernike_coeffs)

    time_name = kalao_time.get_isotime()

    df.to_pickle(f'ncpa_scan_{time_name}.pickle')

    #max_row = df.iloc[df.peak_flux.idxmax()]
    #print(max_row)
    #zernike_coeffs = max_row[-len(zernike_coeffs):].to_numpy()

    peak = display_and_measure(dm_stream, zernike_coeffs, R, Theta, args,
                            update_stream=True)
    print(f'Final peak value: {peak}')
    print(f'Final coefficients: {zernike_coeffs}')

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
    parser.add_argument('-s', action="store", dest="orders_to_skip",
                        default=10, type=int,
                        help='Numbers of orders to skip')
    parser.add_argument('-s', action="store", dest="steps", default=25,
                        type=int, help='Number of steps')
    parser.add_argument('-i', action="store", dest="iterations", default=10,
                        type=int, help='Number of iterations')
    parser.add_argument('-max_flux', action="store", dest="max_flux", default=2**15,
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
    parser.add_argument('-w', action="store", dest="window", default=100,
                        type=int, help='Size of the window to cut out')
    parser.add_argument('-l', action="store", dest="laser_int",
                        default=config.Laser.calib_intensity, type=float,
                        help='Laser intensity')
    parser.add_argument('-a', action="store", dest="img_avg", default=5,
                        type=int, help='Averaging over images')
    parser.add_argument('-p', action="store", dest="peak_window", default=5,
                        type=int, help='Size of window for peak fitting')

    args = parser.parse_args()

    if camera.check_server_status() != CameraServerStatus.UP:
        print('Error connecting to camera. Please try to restart the kalao_camera service'
              )
        exit(-1)

    laser.set_intensity(args.laser_int)

    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, handler)

    if filterwheel.set_position(args.filter_name) == -1:
        print("Error with filter selection")
    sleep(2)

    run(args)
