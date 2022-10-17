#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : fli_stream.py
# @Date : 2021-02-23-14-10
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
fli_stream.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""
import argparse


from time import sleep
from signal import signal, SIGINT
from sys import exit
from pprint import pprint
import numpy as np

from sequencer import system

import FLI
from pyMilk.interfacing.isio_shmlib import SHM


parser = argparse.ArgumentParser(
        description='Opens stream with FLI camera images.')
parser.add_argument('-d', action="store",  dest="dit", type=int, default=1)
parser.add_argument('-c', action="store", dest="center",  default=None, nargs='+', type=int,
                    help='x y position of the window center')
parser.add_argument('-w', action="store", dest="window_size", default=None, type=int,
                    help='Size of the window to cut out. ')

args = parser.parse_args()
dit = args.dit
center = args.center
window = args.window_size


def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected. Exiting.')
    system.camera_service('start')
    print('Restarted kalao_camera service')
    exit(0)


def cut_image(img):

    if window is not None:
        hw = int(np.round(window/2))
        if center is None:
            c = [img.shape[0]/2, img.shape[1]/2]
        else:
            c = center
        img = img[c[0]-hw:c[0]+hw, c[1]-hw:c[1]+hw]

    img = img.astype(float)

    return img


def run(cam):
    # initialise stream

    cam.set_exposure(dit)
    img = cam.take_photo()

    img = cut_image(img)

    # Creating a brand new stream
    shm = SHM('fli_stream', img,
                 location=-1,  # CPU
                 shared=True,  # Shared
                 )

    while True:
        cam.set_exposure(dit)
        img = cam.take_photo()
        img = cut_image(img)
        shm.set_data(img)
        sleep(0.00001)


if __name__ == '__main__':
    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, handler)

    system.camera_service('stop')
    print('Stopped kalao_camera service')

    sleep(2)

    cam = FLI.USBCamera.find_devices()[0]
    pprint(dict(cam.get_info()))
    print('Temperature: ' + str(cam.get_temperature()))
    cam.set_temperature(-30)
    cam.set_exposure(dit)
    run(cam)
