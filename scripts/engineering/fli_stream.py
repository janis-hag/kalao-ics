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

from kalao.hardware import camera

from kalao.definitions.enums import CameraServerStatus


def sig_handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected. Exiting.')
    exit(0)


def run(args):
    if camera.server_status() == CameraServerStatus.UP:
        print('Connecting to camera through REST API')

        while True:
            camera.take_image(exptime=args.exptime)
    else:
        print('Error connecting to camera. Please check the kalao_fli service')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Periodically take FLI camera images.')
    parser.add_argument('--exptime', action="store", dest="exptime",
                        type=float, default=0.001,
                        help='Detector Integration Time')

    args = parser.parse_args()

    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, sig_handler)

    run(args)
