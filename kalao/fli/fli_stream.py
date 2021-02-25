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

import FLI
from pyMilk.interfacing.isio_shmlib import SHM
from time import sleep
from signal import signal, SIGINT
from sys import exit
from pprint import pprint

dit = 1


def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected. Exiting.')
    exit(0)


def run(cam):
    # initialise stream

    cam.set_exposure(dit)
    img =  cam.take_photo()

    # Creating a brand new stream
    shm = SHM('fli_stream', img,
                 location=-1,  # CPU
                 shared=True,  # Shared
                 )

    while True:
        cam.set_exposure(dit)
        img = cam.take_photo()
        shm.set_data(img)
        sleep(0.2)

if __name__ == '__main__':
    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, handler)

    cam = FLI.USBCamera.find_devices()[0]
    pprint(dict(cam.get_info()))
    print('Temperature: '+str(cam.get_temperature()))
    cam.set_temperature(-30)
    cam.set_exposure(dit)
    run(cam)
