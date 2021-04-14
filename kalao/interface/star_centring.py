#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : star_centring.py
# @Date : 2021-04-13-17-10
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
star_centring.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from astropy.io import fits

def fli_view():

    fli_image_name = get_latest_image_path()
    centring_image = fits.getdata(fli_image_name)

    manual_centring_needed = False

    return manual_centring_needed, centring_image

def get_latest_image_path():

    # READ mongodb to find latest filename
    filename = "kALAO.fits"

    return filename

def star_position_pixels(x, y):

    # save x,y into mongodb
    # set manual_centring_needed to false

    return 0