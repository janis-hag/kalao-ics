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

from kalao.interface import star_centering
from kalao.plc import calib_unit, tungsten, adc
from kalao.fli import control
from kalao.utils import database, file_handling

from astropy.io import fits
from time import sleep, time

def scan_calib(scan_range, dit=0.05):

    #tungsten.on()
    for pos in scan_range:
        calib_unit.move(pos)

        control.take_image()

        sleep(10)

        filename, file_date = star_centering.get_temporary_image_path()

        with fits.open(filename, mode = 'update') as hdul:
            hdr = hdul[0].header
            hdr.set('CALIBPOS', pos)
            hdul.flush()
            print(filename)

    tungsten.off()

def scan_adc(scan_range, dit=0.05):

    #tungsten.on()
    adc.rotate(1, scan_range[0])
    adc.rotate(1, scan_range[0] + 90)

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
    for ang in scan_range:
        adc.rotate(1, ang)
        adc.rotate(2, ang+90)

        print(ang)
        sleep(2)

        control.take_image()

        sleep(1)

        image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values'][0]
        print(image_path)
        file_handling.update_header(image_path)


def focus():
    # Focus sequence like coralie
    pass

def create_mosaic():
    # create a 5x5 image grid for initial star centering
    pass
