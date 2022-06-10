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
# - update_temporary_folder( current_folder, temporary_folder)

import sys
import os
from pathlib import Path
#import time
from configparser import ConfigParser
from datetime import datetime, timezone
from astropy.io import fits

from kalao.utils import kalao_time, database
from kalao.fli import camera

from sequencer import system

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')

# Read config file and create a dict for each section where keys is parameter
parser = ConfigParser()
parser.read(config_path)

TemporaryDataStorage = parser.get('FLI', 'TemporaryDataStorage')
Science_folder = parser.get('FLI', 'ScienceDataStorage')
T4root = parser.get('SEQ', 't4root')


def create_night_filepath(tmp_night_folder=None):
    """
    Creates a full filepath including filename. If the destination folder does not exist it is created.

    :return: the generated filepath
    """

    if tmp_night_folder is None:
        tmp_night_folder = create_night_folder()

    filename = 'tmp_KALAO.' + kalao_time.get_isotime() + '.fits'
    filepath = tmp_night_folder+os.sep+filename

    return filepath


def create_night_folder():
    # Prepare temporary and science folder
    # check if folder exists
    # remove temporary folder of previous night if empty

    Tmp_night_folder = os.path.join(TemporaryDataStorage, kalao_time.get_start_of_night())
    Science_night_folder = os.path.join(Science_folder, kalao_time.get_start_of_night())

    # Check if tmp and science folders exist
    if not os.path.exists(Tmp_night_folder):
        os.mkdir(Tmp_night_folder)
    if not os.path.exists(Science_night_folder):
        os.mkdir(Science_night_folder)

    # Remove empty folder in tmp except for current night folder
    for folder in os.listdir(TemporaryDataStorage):
        folder = os.path.join(TemporaryDataStorage, folder)
        if folder != Tmp_night_folder and len(os.listdir(folder)) == 0:
            os.rmdir(folder)

    return Tmp_night_folder


def save_tmp_image(image_path, header_keydict=None):
    '''
    Updates the temporary image header and saves into the archive.

    :param image_path:
    :param header_keydict:
    :return:
    '''
    Science_night_folder = Science_folder+os.sep+kalao_time.get_start_of_night()
    target_path_name = Science_night_folder+os.sep+os.path.basename(image_path)

    if os.path.exists(image_path) and os.path.exists(Science_night_folder):
        update_header(image_path, header_keydict=header_keydict)
        os.rename(image_path, target_path_name)
        # TODO remove write permission

        camera.log_last_image_path(target_path_name)

        return target_path_name
    else:
        database.store_obs_log({'sequencer_log': 'ERROR: unable to save '+image_path+' to '+target_path_name})
        database.store_obs_log({'sequencer_status': 'ERROR'})

        return -1


def update_header(image_path, header_keydict=None):
    '''
    Updates the image header with values from the observing, monitoring, and telemetry logs.

    :param image_path: path to the image to update
    :param header_keydict: dictionary of key:values to add
    :return:
    '''

    # Read DATE-OBS in headers
    # Search start values in log
    # Search end values in log using DATE-OBS and TEXP
    # Compute median values for specific keywords
    # Add HEADER values for start, end, and median.

    # :param obs_category: Observing category keyword.SCIENCE, CALIB, TECHNICAL, TEST, OTHER
    # :param obs_type: Observing type.Can be comma separated list of the following keywords
    # OBJECT, STD, ASTROMETRY, BIAS, DARK, FLAT, SKY, LAMP, FLUX, PSF-CALIBRATOR, FOCUS

    #TODO read telescope generated header and then remove it


    fits_header_config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'fits_header.config')
    header_config = ConfigParser()
    header_config.read(fits_header_config_path)

    default_cards = read_header_cards(header_config, 'Default_cards')

    obs_log_cards = read_header_cards(header_config, 'Obs_log')

    monitoring_cards = read_header_cards(header_config, 'Monitoring')
    # monitoring_cards = dict(header_config.items('Monitoring'))
    # for k in monitoring_cards.keys():
    #     monitoring_cards[k] = monitoring_cards[k].split(',')

    telemetry_cards = read_header_cards(header_config, 'Telemetry')
    # telemetry_cards = dict(header_config.items('Telemetry'))
    # for k in telemetry_cards.keys():
    #     telemetry_cards[k] = telemetry_cards[k].split(',')

    with fits.open(image_path, mode='update') as hdul:
        # Change something in hdul.
        header = hdul[0].header
        dt = datetime.fromisoformat(header['DATE-OBS']).replace(tzinfo=timezone.utc)
        # keys = {'shutter', 'tungsten', 'laser', 'adc1', 'adc2'}

        for key, value_comment in default_cards.items():
            header.set(key.upper(), value_comment[0].strip(), value_comment[1].strip())

        telescope_header, header_path = _get_last_telescope_header()



        # Storing monitoring
        obs_log_status = database.get_obs_log(obs_log_cards.keys(), 1, dt=dt)
        for key, type_comment in obs_log_cards.items():
            # Check if key exists and value not empty
            if key in obs_log_status.keys() and obs_log_status[key]['values']:
                header.set('HIERARCH KAL '+key.upper(), obs_log_status[key]['values'][0], type_comment[1].strip())
            else:
                header.set('HIERARCH KAL '+key.upper(), '', type_comment[1].strip())


        # Storing monitoring
        monitoring_status = database.get_monitoring(monitoring_cards.keys(), 1, dt=dt)
        for key, type_comment in monitoring_cards.items():
            # Check if key exists and value not empty
            if key in monitoring_status.keys() and monitoring_status[key]['values']:
                header.set('HIERARCH KAL '+key.upper(), monitoring_status[key]['values'][0], type_comment[1].strip())
            else:
                header.set('HIERARCH KAL '+key.upper(), '', type_comment[1].strip())

        # Storing telemetry
        telemetry_status = database.get_telemetry(telemetry_cards.keys(), 1, dt=dt)
        for key, type_comment in telemetry_cards.items():
            # Check if key exists and value not empty
            if key in telemetry_status.keys() and telemetry_status[key]['values']:
                header.set('HIERARCH KAL AO '+key.upper(), telemetry_status[key]['values'][0], type_comment[1].strip())
            else:
                header.set('HIERARCH KAL AO '+key.upper(), '', type_comment[1].strip())

        #header_keydict = update_default_header_keydict(default_cards, header_keydict)

        # Add key dictionary given as argument
        if not header_keydict is None:
            for key, value in header_keydict:
                header.set(key.upper(), value) #, type_comment[1].strip())


        # header.set('LASER', monitoring_status['laser']['values'][0], 'short description fro database_definition')
        # header.set('SHUTTER', monitoring_status['shutter']['values'][0], 'short description fro database_definition')
        # header.set('TUNGSTEN', monitoring_status['tungsten']['values'][0], 'short description fro database_definition')
        # header.set('ADC1', monitoring_status['adc1']['values'][0], 'short description fro database_definition')
        # header.set('ADC2', monitoring_status['adc2']['values'][0], 'short description fro database_definition')

        hdul.flush()  # changes are written back to original.fits

    return 0


def add_comment(image_path, comment_string):
    with fits.open(image_path, mode='update') as hdul:
        # Change something in hdul.
        header = hdul[0].header
        header['COMMENT'] = comment_string
        hdul.flush()

    return 0


def read_header_cards(header_config, items_name):

    header_cards = dict(header_config.items(items_name))
    for k in header_cards.keys():
        header_cards[k] = header_cards[k].split(',')

    return header_cards


def update_default_header_keydict(default_cards, header_keydict):

    return header_keydict


def _get_last_telescope_header():
    """
    Reads header file path from database base and returns the header content along with the path

    :return:
    """

    # TODO verify if latest_record['time_utc'] is recent enough
    latest_record = database.get_latest_record('obs_log', key='tcs_header_path')
    tcs_header_path = os.path.join(T4root, latest_record['tcs_header_path'])

    if os.path.exists(tcs_header_path):
        tcs_header = fits.getheader(tcs_header_path)
    else:
        system.print_and_log(('ERROR: header file not found: '+str(tcs_header_path)))
        tcs_header = None

    return tcs_header, tcs_header_path
