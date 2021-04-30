#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : star_centering.py
# @Date : 2021-04-13-17-10
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
star_centering.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from astropy.io import fits
import os
import numpy as np

from kalao.utils import database


def fli_view(realData=False):

	if not realData:
		# Returning fake fli_view for testing purposes
		return fake_data.fake_fli_view()
	else:
        fli_image_path, file_date = get_temporary_image_path()

        if fli_image_path is not None and file_date is not None and os.path.isfile(fli_image_path):
            centering_image = fits.getdata(fli_image_path)
        else:
            centering_image = np.zeros((1024, 1204))

        manual_centering_needed = False

        return manual_centering_needed, centering_image


def _get_image_path(image_type):

    if image_type in ['latest', 'temporary']:
        # READ mongodb to find latest filename
        last_image = database.get_obs_log(['fli_'+image_type+'_image_path'], 1)['fli_'+image_type+'_image_path']
        filename = last_image['values']
        file_date = last_image['time_utc']
        if not last_image['values']:
            # Set to None is list is empty
            filename = None
            file_date = None

        return filename, file_date

    return 1


def get_latest_image_path():

    filename, file_date = _get_image_path('latest')

    return filename, file_date


def get_temporary_image_path():

    filename, file_date = _get_image_path('temporary')

    return filename, file_date


def star_pixel(x, y):

    # save x,y into mongodb
    # set manual_centring_needed to false

    return 0
