#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : fits_handling
# @Date : 2021-08-02-11-55
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
file_handling.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

# TODO create functions:
# - def update_fits_header
# - update_temporary_folder( current_folder, temporary_folder)

import sys
import os
from pathlib import Path
import time
from configparser import ConfigParser
from datetime import datetime
from astropy.io import fits

from kalao.utils import kalao_time, database

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')

# Read config file and create a dict for each section where keys is parameter
parser = ConfigParser()
parser.read(config_path)

Tmp_folder = parser.get('FLI','TemporaryDataStorage')
Science_folder = parser.get('FLI','ScienceDataStorage')

def create_night_folder():
    # Prepare temporary and science folder
    # check if folder exists
    # remove temporary folder of previous night if empty

    Tmp_night_folder = os.path.join(Tmp_folder, kalao_time.get_start_of_night())
    Science_night_folder = os.path.join(Science_folder, kalao_time.get_start_of_night())

    # Check if tmp and science folders exist
    if not os.path.exists(Tmp_night_folder):
        os.mkdir(Tmp_night_folder)
    if not os.path.exists(Science_night_folder):
        os.mkdir(Science_night_folder)

    # Remove empty folder in tmp except for current night folder
    for folder in os.listdir(Tmp_folder):
        folder = os.path.join(Tmp_folder, folder)
        if folder != Tmp_night_folder and len(os.listdir(folder)) == 0:
            os.rmdir(folder)

    return Tmp_night_folder

def save_tmp_picture(image_path):
    Science_night_folder = Science_folder+os.sep+kalao_time.get_start_of_night()
    target_name = Science_night_folder+os.sep+os.path.basename(image_path)

    if os.path.exists(image_path) and os.path.exists(Science_night_folder):
        update_header(image_path)
        os.rename(image_path, target_name)
        return target_name
    else:
        # TODO add log error
        return -1

def update_header(image_path):
    # Read DATE-OBS in header
    # Search start values in log
    # Search end values in log using DATE-OBS and TEXP
    # Compute median values for specific keywords
    # Add HEADER values for start, end, and median.

    with fits.open(image_path, mode='update') as hdul:
        # Change something in hdul.
        header = hdul[0].header
        dt = datetime.fromisoformat(header['DATE-OBS'])
        keys = {'shutter', 'tungsten', 'laser'}
        monitoring_status = database.get_monitoring(keys, 1, dt=dt)
        header.set('LASER', monitoring_status['laser']['values'][0], 'short description fro database_definition')
        header.set('SHUTTER', monitoring_status['shutter']['values'][0], 'short description fro database_definition')
        header.set('TUNGSTEN', monitoring_status['tungsten']['values'][0], 'short description fro database_definition')
        header.set('ADC1', monitoring_status['adc1']['values'][0], 'short description fro database_definition')
        header.set('ADC2', monitoring_status['adc2']['values'][0], 'short description fro database_definition')

        hdul.flush()  # changes are written back to original.fits

    return 0
