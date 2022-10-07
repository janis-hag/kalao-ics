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
import shutil
#import time
from configparser import ConfigParser
from datetime import datetime, timezone
from astropy.io import fits
import pandas as pd
import yaml
from astropy import units
from astropy.coordinates import EarthLocation
from astropy.time import Time

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
FileMask = parser.get('FLI', 'FileMask')
T4root = parser.get('SEQ', 't4root')
FitsHeaderFile = parser.get('SEQ', 'fits_header_file')


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


def save_tmp_image(image_path, sequencer_arguments=None):
    '''
    Updates the temporary image header and saves into the archive.

    :param image_path:
    :param sequencer_arguments: argument list received by the sequencer
    :return:
    '''
    Science_night_folder = Science_folder+os.sep+kalao_time.get_start_of_night()

    # Remove tmp_ from filename
    target_path_name = Science_night_folder+os.sep+os.path.basename(image_path).replace('tmp_', '')

    if os.path.exists(image_path) and os.path.exists(Science_night_folder):
        update_header(image_path, sequencer_arguments=sequencer_arguments)
        shutil.move(image_path, target_path_name)
        # TODO Remove write permission
        # os.chmod(target_path_name, FileMask)

        # TODO possibly add the right UID and GID
        system.print_and_log('Saved: '+target_path_name)
        camera.log_last_image_path(target_path_name)

        return target_path_name
    else:
        database.store_obs_log({'sequencer_log': 'ERROR: unable to save '+image_path+' to '+target_path_name})
        database.store_obs_log({'sequencer_status': 'ERROR'})

        return -1




def update_header(image_path, sequencer_arguments=None):
    """
    Updates the image header with values from the observing, monitoring, and telemetry logs.

    :param image_path: path to the image to update
    :param sequencer_arguments: argumetns received by the sequencer
    :return:
    """

    # Reading the fits definitions
    header_df = _read_fits_defintions()

    # Reindexing with keyword
    header_df.set_index('keyword', drop=False, inplace=True)

    header_df['value']['HIERARCH ESO DPR TECH'] = 'IMAGE'
    header_df['value']['HIERARCH ESO DPR CATG'] = 'TECHNICAL'
    header_df['value']['HIERARCH ESO DPR TYPE'] = ''

    if sequencer_arguments is not None:
        type = sequencer_arguments.get('type')
        if type == 'K_DARK':
            header_df['value']['HIERARCH ESO DPR CATG'] = 'CALIB'
            header_df['value']['HIERARCH ESO DPR TYPE'] = 'DARK'
        elif type == 'K_LMPFLT':
            header_df['value']['HIERARCH ESO DPR CATG'] = 'CALIB'
            header_df['value']['HIERARCH ESO DPR TYPE'] = 'FLAT,LAMP'
        elif type == 'K_TRGOBS':
            header_df['value']['HIERARCH ESO DPR CATG'] = 'SCIENCE'
            header_df['value']['HIERARCH ESO DPR TYPE'] = 'OBJECT'

    print(header_df[['keyword', 'value']])

    with fits.open(image_path, mode='update') as hdul:
        # Change something in hdul.
        fits_header = hdul[0].header

        if 'DATE-OBS' in fits_header.keys():
            dt = datetime.fromisoformat(fits_header['DATE-OBS']).replace(tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(fits_header['DATE']).replace(tzinfo=timezone.utc)


        # Fill default values
        for card in header_df.loc[header_df['keygroup'] == 'default_keys'].itertuples(index=False):
            # TODO add the keywords into the header at the right position in order to keep it sorted.
            header_df = pd.concat([header_df, pd.DataFrame({'keygroup': 'default_keys',
                                                            'keyword': card.keyword,
                                                            'value': card.value,
                                                            'comment': card.comment}, index=[0])])

        # Gather all the logs
        obs_log = database.get_obs_log(header_df.loc[header_df['keygroup'] == 'Obs_log']['value'].tolist(), 1,
                                          dt=dt)

        monitoring_log = database.get_monitoring(header_df.loc[header_df['keygroup'] == 'Monitoring']['value'].tolist(), 1,
                                             dt=dt)

        telemetry_log = database.get_telemetry(header_df.loc[header_df['keygroup'] == 'Telemetry']['value'].tolist(), 1,
                                            dt=dt)

        # obs_log needs to be first as it contains some non-hierarch keywords
        header_df = _add_header_values(header_df=header_df, log_status={**obs_log, **monitoring_log, **telemetry_log}, fits_header=fits_header)

        print(header_df[['keyword','value']])

        # Add telescope header
        telescope_header_df, header_path = _get_last_telescope_header()
        # Remove first part of header
        # TODO set the cutoff keyword in kalao.config
        telescope_header_df = telescope_header_df[(telescope_header_df.keyword == 'OBSERVER' ).idxmax():]

        for card in telescope_header_df.itertuples(index=False):
            # if key starts with ESO search last occurence with same beginning and add keyword afterwards
            if len(card.keyword) < 9:
                card_keyword = card.keyword.upper()
            else:
                card_keyword = 'HIERARCH ' + card.keyword.upper()
            header_df = pd.concat([header_df, pd.DataFrame({'keygroup': 'Telescope',
                                                            'keyword': card_keyword,
                                                            'value': card.value,
                                                            'comment': card.comment}, index=[0])])

        header_df = _dynamic_cards_update(header_df)

        # # Add key dictionary given as argument
        # if not header_keydict is None:
        #     for key, value in header_keydict:
        #         header.set(key.upper(), value) #, type_comment[1].strip())

        header_df = _clean_sort_header(header_df)

        # Remove all cards before updating
        #fits_header.clear()
        for card in header_df.itertuples(index=False):
            print(card.keyword, card.value)
            fits_header.set(card.keyword, card.value, card.comment.strip())

        # Update 'DATE' card

        hdul.verify('silentfix+warn')

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

    tcs_header_path_record = database.get_latest_record('obs_log', key='tcs_header_path')

    tcs_header_path = Path(tcs_header_path_record['tcs_header_path'])

    if tcs_header_path.is_file():
        tcs_header_df = _header_to_df(fits.getheader(tcs_header_path))
    else:
        system.print_and_log(('ERROR: header file not found: '+str(tcs_header_path)))
        tcs_header_df = None

    # TODO uncomment the unlink line in order to remove the tmp fits
    #tcs_header_path.unlink()

    return tcs_header_df, str(tcs_header_path)


def _clean_sort_header(header_df):

    #hdr_df = pd.DataFrame.from_records(hdr.cards, columns=['keyword', 'value', 'comment'])

    # Remove cards with empty keywords
    header_df = header_df[header_df['keyword'].str.strip().astype(bool)]
    header_df.reset_index(drop=True, inplace=True)

    # Search for first HIERARCH keyword (i.e. longer than 8) and split in two header dataframes
    first_hierarch_line = header_df.keyword.str.len().ge(9).idxmax()
    header_head_df = header_df.iloc[:first_hierarch_line]
    header_tail_df = header_df.iloc[first_hierarch_line:].sort_values(by=['keyword'])

    #header_df = header_head_df.append(header_tail_df, ignore_index=True)
    header_df = pd.concat([header_head_df, header_tail_df], ignore_index=True)

    # To be verified of HIERARCH keyword is needed
    #header_tail_df['keyword'] = 'HIERARCH ' + header_tail_df['keyword'].astype(str)

    return header_df


def _read_fits_defintions():
    '''
    Reads the fits header file definition YAML file and returns a pandas dataframe with
    the following keys: keyword, value, comment

    :return: pandas dataframe with the fits definitions
    '''

    with open(FitsHeaderFile, 'r') as f:
        y = yaml.safe_load(f)

    yaml_dic = pd.json_normalize(y)

    # Put keygroup as first column
    col = yaml_dic.pop('keygroup')
    yaml_dic.insert(0, col.name, col)

    return yaml_dic


def _header_to_df(header):
    '''
    Reads a fits header and reformats it into a dataframe

    :param header:
    :return: header dataframe
    '''
    header_df = []

    for keyword in header.keys():
        header_df.append({
            'keyword': keyword,
            'value': header[keyword],
            'comment': header.comments[keyword]})

    header_df = pd.DataFrame(header_df)

    return header_df


def _add_header_values(header_df, log_status, fits_header):
    '''
    Add the values from the log to the header dataframe

    :param header_df:
    :return: header_df: with values completed
    '''

    for idx, card in header_df.iterrows():
        # Do not modify default_keys
        if card.keygroup == 'default_keys':
            continue

        elif card.keygroup == 'FLI' and card.keyword in fits_header.keys():
            header_df.loc[idx, 'value'] = fits_header[card.keyword]
            header_df.loc[idx,'comment'] = card.comment.strip()

        #header.set(card.keyword.upper(), card.value, card.comment.strip())
        elif card.value in log_status.keys() and log_status[card.value]['values']:
            header_df.loc[idx,'value'] = log_status[card.value]['values'][0]
            header_df.loc[idx,'comment'] = card.comment.strip()
            #card.keyword =  'ESO '+ keycode + ' ' + card.keyword.upper()
            #header.set('HIERARCH ESO ' + keycode + ' ' + card.keyword.upper(), log_status[card.keyword]['values'][0],
            #           card.comment.strip())

        else:
            #card.value = log_status[card.keyword]['values'][0]
            header_df.loc[idx, 'value'] = ''
            header_df.loc[idx,'comment'] = card.comment.strip()
            #card.keyword = 'ESO ' + keycode + ' ' + card.keyword.upper()
            #header.set('HIERARCH ESO ' + keycode + ' ' + card.keyword.upper(), '', card.comment.strip())

    return header_df


def _fill_log_header_keys(header, header_df, log_status, keycode):
    '''
    Fills the fits header with values from the log based of header keys defined in header_df

    :param header:
    :param header_df:
    :param log_status:
    :param keycode:
    :return:
    '''

    for card in header_df.itertuples(index=False):
        #header.set(card.keyword.upper(), card.value, card.comment.strip())
        if card.keyword in log_status.keys() and log_status[card.keyword]['values']:
            header.set('HIERARCH ESO ' + keycode + ' ' + card.keyword.upper(), log_status[card.keyword]['values'][0],
                       card.comment.strip())
        else:
            header.set('HIERARCH ESO ' + keycode + ' ' + card.keyword.upper(), '', card.comment.strip())

    return header


def _dynamic_cards_update(header_df):

    # TODO add RA comment: [deg] 16:22:51.8 RA (J2000) pointing
    # TODO add DEC comment: [deg] -23:07:08.8 DEC (J2000) pointing
    # TODO add radecsys value in EQUINOX comment


    # Change shutter comment to "Shutter open" or "Shutter closed" and put only T/F in value

    # idx = header_df.index[header_df['keyword'] == 'HIERARCH ESO INS SHUT ST']
    #
    # if len(idx>0):
    #     idx = idx[0]
    header_df['comment']['HIERARCH ESO INS SHUT ST'] = header_df['comment']['HIERARCH ESO INS SHUT ST'] + ' ' \
                                                       + header_df['value']['HIERARCH ESO INS SHUT ST'].lower()

    if header_df['value']['HIERARCH ESO INS SHUT ST'] == 'open':
        header_df['value']['HIERARCH ESO INS SHUT ST'] = 'T'
    else:
        header_df['value']['HIERARCH ESO INS SHUT ST'] = 'F'

    date_obs = header_df.loc[header_df['keyword'] == 'DATE-OBS']['value'].values[0]

    dt_obs = datetime.fromisoformat(date_obs).replace(tzinfo=timezone.utc)

    la_silla_coord = EarthLocation.from_geocentric(1838554.9580025, -5258914.42492168, -3099898.78073271, units.m)

    astro_time = Time(date_obs, scale='utc', location=la_silla_coord)
    sidereal_seconds = astro_time.sidereal_time('mean').hour*3600
    #astro_time.sidereal_time('mean').to_string(units.hour, sep=':')

    # Update MJD-OBS
    # idx = header_df.index[header_df['keyword'] == 'MJD-OBS']
    # if len(idx>0):
    #     idx = idx[0]
    header_df['comment']['MJD-OBS'] = date_obs
    header_df['value']['MJD-OBS'] = str(kalao_time.get_mjd(dt_obs))[2:]

    # Update UTC
    # idx = header_df.index[header_df['keyword'] == 'UTC']
    # if len(idx>0):
    #     idx = idx[0]
    header_df['comment']['UTC'] = '[s] '+dt_obs.strftime('%H:%M:%S.%f')[:-3] + ' UTC'
    header_df['value']['UTC'] = str((dt_obs.hour * 60 + dt_obs.minute) * 60 + dt_obs.second) \
                                    + '.' + str(dt_obs.microsecond)

    # # Update LST
    # idx = header_df.index[header_df['keyword'] == 'LST']
    # if len(idx>0):
    #     idx = idx[0]
    header_df['comment']['LST'] = '[s] '+ astro_time.sidereal_time('mean').to_string(units.hour, sep=':')[:-1] + ' LST'
    header_df['value']['LST'] = astro_time.sidereal_time('mean').hour*3600

    return header_df
