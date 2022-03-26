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
from pprint import pprint
import numpy as np
import pandas as pd

from sequencer import system
#from kalao.plc import filterwheel, laser
from kalao.utils import kalao_time

from kalao.fli import FLI
from pyMilk.interfacing.isio_shmlib import SHM


def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected. Exiting.')
    system.camera_service('start')
    print('Restarted kalao_camera service')
    exit(0)


def cut_image(img, window, center):

    if window is not None:
        hw = int(np.round(window/2))
        if center is None:
            c = [img.shape[0]/2, img.shape[1]/2]
        else:
            c = center
        img = img[c[0]-hw:c[0]+hw, c[1]-hw:c[1]+hw]

    img = img.astype(float)

    return img


def run(cam, args):
    # initialise stream
    dit = args.dit
    orders_to_correct = args.orders_to_correct
    steps = args.steps
    iterations = args.iterations
    max_flux = args.max_flux
    min_flux = args.min_flux
    max_dit = args.max_dit
    filter_name = args.filter_name
    min_step = args.min_step
    center = args.center
    window = args.window_size

    new_dit = dit

    while(True):
        # Search optimal dit
        cam.set_exposure(new_dit)
        img = cam.take_photo()
        img = cut_image(img, window, center)

        print(new_dit, img.max())
        if img.max() >= max_flux:
            new_dit = int(np.floor(0.8 * new_dit))
            if new_dit <= 1:
                print('Max flux '+str(img.max())+' above max permitted value ' + str(max_flux))
                sys.exit(1)
            continue
        elif img.max() <= min_flux:
            new_dit = int(np.ceil(1.2 * new_dit))
            if new_dit >= max_dit:
                print('Max flux '+str(img.max())+' below minimum permitted value: ' + str(min_flux))
                sys.exit(1)
            continue
        else:
            break

    print('Setting DIT to: '+str(new_dit))
    cam.set_exposure(new_dit)
    img = cam.take_photo()
    img = cut_image(img, window, center)

    peak_value = img.max()

    # Creating a brand new stream
    shm = SHM('fli_stream', img,
                 location=-1,  # CPU
                 shared=True,  # Shared
                 )

    # bmc_zernike_coeff OSA sorted orders

    # Order 0 piston

    zernike_shm = SHM('bmc_zernike_coeff')
    zernike_array =  zernike_shm.get_data(check=False)

    if orders_to_correct > len(zernike_array):
        orders_to_correct = len(zernike_array)
        print("Correcting maximum number of orders: "+str(len(zernike_array)) )
    else:
        print('Correcting '+str(orders_to_correct)+' orders.')

    # -1.75 1.75
    zernike_array[:] = 0

    df = pd.DataFrame(columns=['peak_flux', 'iteration', 'order', 'step']+np.arange( len(zernike_array)).tolist())

    # Initial step size

    # Initialise values to zero
    zernike_shm.set_data(zernike_array.astype(zernike_shm.nptype))

    for i in range(iterations):
        print('Iteration: '+str(i))

        for order in range(1, orders_to_correct):
            print('Optimising order: '+str(order))
            zernike_step = 1.75 / 2  # / steps

            # Reset value to zero before starting search
            zernike_array[order] = 0

            img = cam.take_photo()
            img = cut_image(img, window, center)

            peak_array = np.zeros((3,2))

            peak_array[1][0] = img.max()
            peak_array[1][1] = zernike_array[order]

            for step in range(steps):
                if zernike_step < min_step:
                    # Stop search if step get too small for this order
                    break

                print('Step '+str(step)+'. Zernike amplitude '+str(zernike_array[order])+'. Max flux: '+str(img.max()))

                up = zernike_array[order] + zernike_step
                down = zernike_array[order] - zernike_step

                # Test up
                zernike_array[order] = up

                zernike_shm.set_data(zernike_array.astype(zernike_shm.nptype))

                #cam.set_exposure(dit)
                img = cam.take_photo()
                img = cut_image(img, window, center)

                peak_array[2][0] = img.max()
                peak_array[2][1] = zernike_array[order]

                # Test down
                zernike_array[order] = down

                zernike_shm.set_data(zernike_array.astype(zernike_shm.nptype))

                #cam.set_exposure(dit)
                img = cam.take_photo()
                img = cut_image(img, window, center)

                # Down value
                peak_array[0][0] = img.max()
                peak_array[0][1] = zernike_array[order]

                #get zernike value of max flux
                zernike_array[order] = peak_array[peak_array[:, 0].argmax(), 1]

                # if peak_down < peak_up:
                #     zernike_array[order] = up
                #     img = cam.take_photo()
                #     img = cut_image(img, window, center)

                df = df.append(pd.Series(np.concatenate((np.array([peak_array.max(),i, order, step]), zernike_array)),
                                         index=df.columns), ignore_index=True)

                zernike_step = zernike_step/2

                shm.set_data(img)
                sleep(0.00001)

                # Set new value of center
                peak_array[1][0] = peak_array[:,0].max()
                peak_array[1][1] = zernike_array[order]

            #zernike_step = zernike_array[order]/steps

            print(zernike_array)

    df.to_pickle('ncpa_scan_'+kalao_time.get_isotime()+'.pickle')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run open-loop NCPA optimisation.')
    parser.add_argument('-d', action="store", dest="dit", type=int, default=1, help="Science camera integration time")
    parser.add_argument('-o', action="store", dest="orders_to_correct", default=10, type=int,
                        help='Numbers of orders to correct')
    parser.add_argument('-s', action="store", dest="steps", default=25, type=int,
                        help='Number of steps')
    parser.add_argument('-i', action="store", dest="iterations", default=10, type=int,
                        help='Number of iterations')
    parser.add_argument('-max', action="store", dest="max_flux", default=2**15, type=float,
                        help='Maximum flux to have on the FLI')
    parser.add_argument('-min_flux', action="store", dest="min_flux", default=2**11, type=int,
                        help='Minimum flux to have on the FLI')
    parser.add_argument('-max_dit', action="store", dest="max_dit", default=20, type=int,
                        help='Maximum dit of the FLI')
    parser.add_argument('-filter', action="store", dest="filter_name", default='nd',
                        help='Filter name to use')
    parser.add_argument('-min_step', action="store", dest="min_step", default=0.01, type=float,
                        help='Minimum step size for convergence')
    parser.add_argument('-c', action="store", dest="center", default=[512, 512], nargs='+', type=int,
                        help='x y position of the window center')
    parser.add_argument('-w', action="store", dest="window_size", default=100, type=int,
                        help='Size of the window to cut out. ')

    args = parser.parse_args()
    dit = args.dit
    # orders_to_correct = args.orders_to_correct
    # steps = args.steps
    # iterations = args.iterations
    # max_flux = args.max_flux
    # min_flux = args.min_flux
    # max_dit = args.max_dit
    filter_name = args.filter_name
    # min_step = args.min_step
    # center = args.center
    # window = args.window_size

    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, handler)

    system.camera_service('stop')
    print('Stopped kalao_camera service')

    #laser.set_intensity(0.3)

    #if filterwheel.set_position(filter_name) == -1:
    #    print("Error with filter selection")
    #sleep(2)

    cam = FLI.USBCamera.find_devices()[0]
    pprint(dict(cam.get_info()))
    print('Temperature: ' + str(cam.get_temperature()))
    cam.set_temperature(-30)
    cam.set_exposure(dit)
    run(cam, args)
