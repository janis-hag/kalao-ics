#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : nuvu_stream_process
# @Date : 2022-02-11-10-21
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
nuvu_stream_process.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from pyMilk.interfacing.isio_shmlib import SHM
from time import sleep
from signal import signal, SIGINT
from sys import exit
import numpy as np

def handler(signal_received, frame):
    # Handle any cleanup here
    print('\nSIGINT or CTRL-C detected. Exiting.')
    # TODO close stream
    #system.camera_service('start')
    #print('Restarted kalao_camera service')
    exit(0)


def run():
    # initialise stream
    cam = SHM('nuvu_raw')

    # Get initial data
    data = cam.get_data(check=True)[4:-2, ::8].astype(np.int16)

    # Create stream
    nuvu_out_stream = SHM('nuvu_proc_stream', data, # 30x30 int16 np.array
                 location=-1, # CPU
                 shared=True, # Shared
                )


    while True:
        data = cam.get_data(check=True)[4:-2, ::8].astype(np.int16)
        # Get new data and refresh stream
        nuvu_out_stream.set_data(data)


if __name__ == '__main__':
    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, handler)

    run()