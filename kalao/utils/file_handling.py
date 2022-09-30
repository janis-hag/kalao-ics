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
import pandas as pd
import yaml

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
    target_path_name = Science_night_folder+os.sep+os.path.basename(image_path)

    if os.path.exists(image_path) and os.path.exists(Science_night_folder):
        update_header(image_path, sequencer_arguments=sequencer_arguments)
        os.rename(image_path, target_path_name)
        # TODO remove write permission

        camera.log_last_image_path(target_path_name)

        return target_path_name
    else:
        database.store_obs_log({'sequencer_log': 'ERROR: unable to save '+image_path+' to '+target_path_name})
        database.store_obs_log({'sequencer_status': 'ERROR'})

        return -1




def update_header(image_path, sequencer_arguments=None):
    '''
    Updates the image header with values from the observing, monitoring, and telemetry logs.

    :param image_path: path to the image to update
    :param sequencer_arguments: argumetns received by the sequencer
    :return:
    '''

    # TODO add date-obs as comment for MJD-OBS
    # TODO give UTC value is seconds and add UTC HMS in comment: [s] 00:19:38.000 UTC
    # TODO give LST value is seconds and add UTC HMS in comment: [s] 17:15:25.278 LST
    # TODO add RA comment: [deg] 16:22:51.8 RA (J2000) pointing
    # TODO add DEC comment: [deg] -23:07:08.8 DEC (J2000) pointing
    # TODO add radecsys value in EQUINOX comment
    # TODO add in shutter comment "Shutter open" or "Shutter closed" and put only T/F in value

    header_df = _read_fits_defintions()

    if sequencer_arguments is not None:
        type = sequencer_arguments.get('type')
        if type == 'K_DARK':
            header_df['DPR CATG']['value'] = 'CALIB'
            header_df['DPR TYPE']['value'] = 'DARK'
        elif type == 'K_LMPFLT':
            header_df['DPR CATG']['value'] = 'CALIB'
            header_df['DPR TYPE']['value'] = 'FLAT,LAMP'
        elif type == 'K_TRGOBS':
            header_df['DPR CATG']['value'] = 'SCIENCE'
            header_df['DPR TYPE']['value'] = 'OBJECT'
        else:
            header_df['DPR CATG']['value'] = 'TECHNICAL'
            header_df['DPR TYPE']['value'] = ''
    #
    # dpr_values = {}
    # dpr_values['TECH'] = {'values': 'IMAGE'}
    # if sequencer_arguments is not None:
    #     type = sequencer_arguments.get('type')
    #     if type == 'K_DARK':
    #         dpr_values['CATG'] = {'values': 'CALIB'}
    #         dpr_values['TYPE'] = {'values': 'DARK'}
    #     elif type == 'K_LMPFLT':
    #         dpr_values['CATG'] = {'values': 'CALIB'}
    #         dpr_values['TYPE'] = {'values': 'FLAT,LAMP'}
    #     elif type == 'K_TRGOBS':
    #         dpr_values['CATG'] = {'values': 'SCIENCE'}
    #         dpr_values['TYPE'] = {'values': 'OBJECT'}
    # else:
    #     dpr_values['CATG'] = {'values': 'TECHNICAL'}
    #     dpr_values['TYPE'] = {'values': ''}


    # header_definitions_df = _read_fits_defintions()
    #
    # header_df = []
    #
    # header_df.append({
    #     'keyword': 'DPR TECH',
    #     'value': 'IMAGE',
    #     'comment': 'Observation technique'})
    #
    # if sequencer_arguments is not None:
    #     type = sequencer_arguments.get('type')
    #     if type == 'K_DARK':
    #         header_df.append({
    #             'keyword': 'DPR CATG',
    #             'value': 'CALIB',
    #             'comment': 'Observation category'})
    #         header_df.append({
    #             'keyword': 'DPR TYPE',
    #             'value': 'DARK',
    #             'comment': 'Observation type'})
    #     elif type == 'K_LMPFLT':
    #         header_df.append({
    #             'keyword': 'DPR CATG',
    #             'value': 'CALIB',
    #             'comment': 'Observation category'})
    #         header_df.append({
    #             'keyword': 'DPR TYPE',
    #             'value': 'FLAT,LAMP',
    #             'comment': 'Observation type'})
    #     elif type == 'K_TRGOBS':
    #         header_df.append({
    #             'keyword': 'DPR CATG',
    #             'value': 'SCIENCE',
    #             'comment': 'Observation category'})
    #         header_df.append({
    #             'keyword': 'DPR TYPE',
    #             'value': 'OBJECT',
    #             'comment': 'Observation type'})
    # else:
    #     header_df.append({
    #             'keyword': 'DPR CATG',
    #             'value': 'TECHNICAL',
    #             'comment': 'Observation category'})
    #     header_df.append({
    #         'keyword': 'DPR TYPE',
    #         'value': '',
    #         'comment': 'Observation type'})
    #
    # header_df = pd.DataFrame(header_df)


    with fits.open(image_path, mode='update') as hdul:
        # Change something in hdul.
        header = hdul[0].header

        if 'DATE-OBS' in header.keys():
            dt = datetime.fromisoformat(header['DATE-OBS']).replace(tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(header['DATE']).replace(tzinfo=timezone.utc)


        # Add default keys
        # for card in header_df.loc[header_df['keygroup'] == 'default_keys'].itertuples(index=False):
        #     header.set(card.keyword.upper(), card.value, card.comment.strip())

        # Create header dataframe and fill all the headers at the end.
        for card in header_df.loc[header_df['keygroup'] == 'default_keys'].itertuples(index=False):
            # TODO add the keywords into the header at the right position in order to keep it sorted.
            header_df.append({'keyword': card.keyword, 'value': card.value, 'comment': card.comment}, ignore_index=True)


        # # TODO add dpr catg, tech, and tpye value along with comment (dpr_tech should always be 'image')
        # header_df.loc[header_df['keygroup'] == 'eso_dpr'] = _add_header_values(
        #                       header_df=header_df.loc[header_df['keygroup'] == 'eso_dpr'],
        #                       log_status=dpr_values)

        # Add monitoring_log keys
        # header = _fill_log_header_keys(header,
        #                       header_df = header_df.loc[header_df['keygroup'] == 'Monitoring'],
        #                       log_status = database.get_monitoring(header_df.loc[header_df['keygroup'] == 'Monitoring']['keyword'].tolist(), 1, dt=dt),
        #                       keycode = 'INS')

        header_df.loc[header_df['keygroup'] == 'Monitoring'] = _add_header_values(
                              header_df=header_df.loc[header_df['keygroup'] == 'Monitoring'],
                              log_status=database.get_monitoring(header_df.loc[header_df['keygroup'] == 'Monitoring']['keyword'].tolist(), 1, dt=dt))

        # Add Telemetry keys
        # header = _fill_log_header_keys(header,
        #                       header_df = header_df.loc[header_df['keygroup'] == 'Telemetry'],
        #                       log_status = database.get_telemetry(header_df.loc[header_df['keygroup'] == 'Telemetry']['keyword'].tolist(), 1, dt=dt),
        #                       keycode = 'INS AO')

        header_df.loc[header_df['keygroup'] == 'Telemetry'] = _add_header_values(
                              header_df=header_df.loc[header_df['keygroup'] == 'Telemetry'],
                              log_status=database.get_telemetry(header_df.loc[header_df['keygroup'] == 'Telemetry']['keyword'].tolist(), 1, dt=dt))

        # Add obs_log keys
        # header = _fill_log_header_keys(header,
        #                       header_df = header_df.loc[header_df['keygroup'] == 'Obs_log'],
        #                       log_status = database.get_telemetry(header_df.loc[header_df['keygroup'] == 'Telemetry']['keyword'].tolist(), 1, dt=dt),
        #                       keycode = 'OBS')

        header_df.loc[header_df['keygroup'] == 'Obs_log'] = _add_header_values(
                              header_df=header_df.loc[header_df['keygroup'] == 'Obs_log'],
                              log_status=database.get_obs_log(header_df.loc[header_df['keygroup'] == 'Obs_log']['keyword'].tolist(), 1, dt=dt))

        # Add telescope header

        telescope_header_df, header_path = _get_last_telescope_header()
        # Remove first part of header
        # TODO set the cutoff keyword in kalao.config
        telescope_header_df = telescope_header_df[(telescope_header_df.keyword == 'OBSERVER' ).idxmax():]

        for card in telescope_header_df.itertuples(index=False):
            # if key starts with ESO search last occurence with same beginning and add keyword afterwards
            if len(card.keyword) < 8:
                card_keyword = card.keyword.upper()
            else:
                card_keyword = 'ESO TEL ' + card.keyword.upper()
            #header_df.set(card_keyword, card.value, card.comment.strip())
            header_df.append({'keyword': card_keyword, 'value': card.value, 'comment': card.comment}, ignore_index=True)


        # # Add key dictionary given as argument
        # if not header_keydict is None:
        #     for key, value in header_keydict:
        #         header.set(key.upper(), value) #, type_comment[1].strip())

        header_df = _clean_sort_header(header_df)

        # Remove all cards before updating
        hdul.clear()
        for card in header_df.itertuples(index=False):
            header_df.set(card.keyword, card.value, card.comment.strip())

        hdul.verify('silentfix+warn')

        hdul.flush()  # changes are written back to original.fits

    return 0


# def update_header_obsolete(image_path, header_keydict=None):
#     '''
#     OBSOLETE version, use update_header function instead.
#
#     Updates the image header with values from the observing, monitoring, and telemetry logs.
#
#     :param image_path: path to the image to update
#     :param header_keydict: dictionary of key:values to add
#     :return:
#     '''
#
#     # Read DATE-OBS in headers
#     # Search start values in log
#     # Search end values in log using DATE-OBS and TEXP
#     # Compute median values for specific keywords
#     # Add HEADER values for start, end, and median.
#
#     # :param obs_category: Observing category keyword.SCIENCE, CALIB, TECHNICAL, TEST, OTHER
#     # :param obs_type: Observing type.Can be comma separated list of the following keywords
#     # OBJECT, STD, ASTROMETRY, BIAS, DARK, FLAT, SKY, LAMP, FLUX, PSF-CALIBRATOR, FOCUS
#
#
#     fits_header_config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'fits_header.config')
#     header_config = ConfigParser()
#     header_config.read(fits_header_config_path)
#
#     default_cards = read_header_cards(header_config, 'Default_cards')
#
#     obs_log_cards = read_header_cards(header_config, 'Obs_log')
#
#     monitoring_cards = read_header_cards(header_config, 'Monitoring')
#     #monitoring_cards = dict(header_config.items('Monitoring'))
#     for k in monitoring_cards.keys():
#          monitoring_cards[k] = monitoring_cards[k].split(',')
#
#     telemetry_cards = read_header_cards(header_config, 'Telemetry')
#     #telemetry_cards = dict(header_config.items('Telemetry'))
#     for k in telemetry_cards.keys():
#         telemetry_cards[k] = telemetry_cards[k].split(',')
#
#     with fits.open(image_path, mode='update') as hdul:
#         # Change something in hdul.
#         header = hdul[0].header
#
#         if 'DATE-OBS' in header.keys():
#             dt = datetime.fromisoformat(header['DATE-OBS']).replace(tzinfo=timezone.utc)
#         else:
#             dt = datetime.fromisoformat(header['DATE']).replace(tzinfo=timezone.utc)
#
#         # keys = {'shutter', 'tungsten', 'laser', 'adc1', 'adc2'}
#
#         for key, value_comment in default_cards.items():
#             header.set(key.upper(), value_comment[0].strip(), value_comment[1].strip())
#
#         # Adding telescope header
#         telescope_header, header_path = _get_last_telescope_header()
#         header.extend(telescope_header.cards, unique=True)
#
#
#         # Storing monitoring
#         obs_log_status = database.get_obs_log(obs_log_cards.keys(), 1, dt=dt)
#         for key, type_comment in obs_log_cards.items():
#             # Check if key exists and value not empty
#             if key in obs_log_status.keys() and obs_log_status[key]['values']:
#                 header.set('HIERARCH ESO INS '+key.upper(), obs_log_status[key]['values'][0], type_comment[1].strip())
#             else:
#                 header.set('HIERARCH ESO INS '+key.upper(), '', type_comment[1].strip())
#
#
#         # Storing monitoring
#         monitoring_status = database.get_monitoring(monitoring_cards.keys(), 1, dt=dt)
#         for key, type_comment in monitoring_cards.items():
#             # Check if key exists and value not empty
#             if key in monitoring_status.keys() and monitoring_status[key]['values']:
#                 header.set('HIERARCH ESO INS '+key.upper(), monitoring_status[key]['values'][0], type_comment[1].strip())
#             else:
#                 header.set('HIERARCH ESO INS '+key.upper(), '', type_comment[1].strip())
#
#         # Storing telemetry
#         telemetry_status = database.get_telemetry(telemetry_cards.keys(), 1, dt=dt)
#         for key, type_comment in telemetry_cards.items():
#             # Check if key exists and value not empty
#             if key in telemetry_status.keys() and telemetry_status[key]['values']:
#                 header.set('HIERARCH ESO INS AO '+key.upper(), telemetry_status[key]['values'][0], type_comment[1].strip())
#             else:
#                 header.set('HIERARCH ESO INS AO '+key.upper(), '', type_comment[1].strip())
#
#         #header_keydict = update_default_header_keydict(default_cards, header_keydict)
#
#         # Add key dictionary given as argument
#         if not header_keydict is None:
#             for key, value in header_keydict:
#                 header.set(key.upper(), value) #, type_comment[1].strip())
#
#
#         # header.set('LASER', monitoring_status['laser']['values'][0], 'short description fro database_definition')
#         # header.set('SHUTTER', monitoring_status['shutter']['values'][0], 'short description fro database_definition')
#         # header.set('TUNGSTEN', monitoring_status['tungsten']['values'][0], 'short description fro database_definition')
#         # header.set('ADC1', monitoring_status['adc1']['values'][0], 'short description fro database_definition')
#         # header.set('ADC2', monitoring_status['adc2']['values'][0], 'short description fro database_definition')
#
#         hdul.flush()  # changes are written back to original.fits
#
#     return 0


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


def _clean_sort_header(hdr):

    hdr_df = pd.DataFrame.from_records(hdr.cards, columns=['keyword', 'value', 'comment'])

    # Remove cards with empty keywords
    hdr_df = hdr_df[hdr_df['keyword'].str.strip().astype(bool)]


    # Search for first HIERARCH keyword (i.e. longer than 8) and split in two header dataframes
    first_hierarch_line = hdr_df.keyword.str.len().ge(9).idxmax()
    header_head_df = hdr_df.iloc[:first_hierarch_line]
    header_tail_df = hdr_df.iloc[first_hierarch_line:].sort_values(by=['keyword'])

    header_df = header_head_df.append(header_tail_df, ignore_index=True)

    # To be verified of HIERARCH keyword is needed
    #header_tail_df['keyword'] = 'HIERARCH ' + header_tail_df['keyword'].astype(str)

    return header_df


def _read_fits_defintions():
    '''
    Reads the fits header file defintion and return a pandas dataframe

    :return: pandas dataframe with the fits definitons
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


def _add_header_values(header_df, log_status):
    '''
    Add hte values from the log to the header dataframe

    :param header_df:
    :return:
    '''

    for card in header_df.itertuples(index=False):
        #header.set(card.keyword.upper(), card.value, card.comment.strip())
        if card.keyword in log_status.keys() and log_status[card.keyword]['values']:
            card.value = log_status[card.keyword]['values'][0]
            card.commment = card.comment.strip()
            #card.keyword =  'ESO '+ keycode + ' ' + card.keyword.upper()
            #header.set('HIERARCH ESO ' + keycode + ' ' + card.keyword.upper(), log_status[card.keyword]['values'][0],
            #           card.comment.strip())
        else:
            #card.value = log_status[card.keyword]['values'][0]
            card.value = ''
            card.commment = card.comment.strip()
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
