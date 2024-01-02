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
from signal import SIGINT, signal
from sys import exit

import numpy as np

from kalao.cacao import toolbox
from kalao.fli import FLI, camera

from kalao.definitions.enums import CameraServerStatus

import config

fli_stream = toolbox.open_or_create_stream(config.Streams.FLI, (1024, 1024),
                                           np.uint16)


def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected. Exiting.')
    exit(0)


def run(args):
    camera_service_status = camera.check_server_status()

    if camera_service_status == CameraServerStatus.DOWN:
        print('Connecting to camera directly')

        cam = FLI.USBCamera.find_devices()[0]
        cam.set_temperature(-30)

        while True:
            cam.set_exposure(int(args.dit * 1000))
            img = cam.take_photo()
            fli_stream.set_data(img, True)
    elif camera_service_status == CameraServerStatus.UP:
        print('Connecting to camera through REST API')

        while True:
            camera.take_frame(args.dit)
    else:
        print(
            'Error connecting to camera. Please try to stop or restart the kalao_fli service'
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Periodically put FLI camera images into fli_stream.')
    parser.add_argument('-d', action="store", dest="dit", type=float,
                        default=0.001, help='Detector Integration Time')

    args = parser.parse_args()

    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, handler)

    run(args)
