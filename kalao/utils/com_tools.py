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
from kalao.plc import calib_unit, tungsten
from kalao.fli import control

from astropy.io import fits
from time import sleep

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
