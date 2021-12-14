#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : com_tools.py
# @Date : 2021-05-07-15-35
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
com_tools.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

import numpy as np

from astropy.io import fits
from time import sleep, time

from kalao.interface import star_centering
from kalao.plc import calib_unit, tungsten, adc
from kalao.fli import camera
from kalao.utils import database, file_handling



def scan_calib(scan_range, dit=0.05):

    #tungsten.on()
    for pos in scan_range:
        calib_unit.move(pos)

        camera.take_image()

        sleep(10)

        filename, file_date = star_centering.get_temporary_image_path()

        with fits.open(filename, mode = 'update') as hdul:
            hdr = hdul[0].header
            hdr.set('CALIBPOS', pos)
            hdul.flush()
            print(filename)

    tungsten.off()

def scan_adc(scan_range1, scan_range2, dit=0.001):

    #tungsten.on()
    adc.rotate(1, scan_range1[0])
    adc.rotate(2, scan_range2[0])

    start = time()
    while not (adc.status(1)['sStatus'] == 'STANDING' and adc.status(1)['sStatus'] == 'STANDING'):
        # Timeout after 5 minutes
        print('.', end='')
        if time() - start > 5*60:
            print('')
            print("TIMEOUT")
            return -1

    print('')
    print('Starting measures')
    for i in np.min(len(scan_range1), len(scan_range2)):
        ang1 = scan_range1[i]
        ang2 = scan_range1[i]
        adc.rotate(1, ang1)
        adc.rotate(2, ang2)

        print(ang)
        sleep(5)

        camera.take_image(dit=dit)

        sleep(1)

        image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values'][0]
        print(image_path)
        file_handling.update_header(image_path)
        file_handling.add_comment(image_path, 'adc1: '+str(ang1)+', adc2: '+str(ang2))

    return 0


def focus():
    # Focus sequence like coralie
    pass

def create_mosaic():
    # create a 5x5 image grid for initial star centering
    pass
