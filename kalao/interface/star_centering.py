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
from skimage.transform import resize
from scipy import stats

from kalao.utils import database
from kalao.cacao import fake_data


def fli_view(binfactor=1, x=512, y=512, realData=True):

    if not realData:
        # Returning fake fli_view for testing purposes
        return False, fake_data.fake_fli_view()
    else:
        fli_image_path, file_date = get_last_image_path()

        if fli_image_path is not None and file_date is not None and os.path.isfile(fli_image_path):
            centering_image = fits.getdata(fli_image_path)
            if binfactor == 4:
                centering_image = resize(centering_image, (centering_image.shape[0] // 4, centering_image.shape[1] // 4),
                       anti_aliasing=True)
            # if binning other that 4 we need to cut edges for the final image to be 256
            centering_image, min_value, max_value = stats.sigmaclip(centering_image, low=2.0, high=2.0)
        else:
            centering_image = np.zeros((256, 256))

        manual_centering_needed = False

        return manual_centering_needed, centering_image, file_date


# TODO move the following functions to file_handling or fli.camera

def _get_image_path(image_type):

    if image_type in ['last', 'temporary']:
        # READ mongodb to find latest filename
        last_image = database.get_latest_record('obs_log', key='fli_'+image_type+'_image_path')
        if last_image.get('fli_'+image_type+'_image_path'):
            filename = last_image['fli_'+image_type+'_image_path']
            file_date = last_image['time_utc']
        else:
            # Set to None is list is empty
            filename = None
            file_date = None

        return filename, file_date

    return -1


def get_last_image_path():

    filename, file_date = _get_image_path('last')

    return filename, file_date


def get_temporary_image_path():

    filename, file_date = _get_image_path('temporary')

    return filename, file_date


def star_pixel(x, y):

    # save x,y into mongodb
    # set manual_centering_needed to false

    return 0
