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

import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from astropy import units as u
from astropy.coordinates import Angle
from astropy.io import fits
from astropy.time import Time

from kalao import euler
from kalao.utils import database, kalao_string, kalao_time, starfinder

import yaml

from kalao.definitions.enums import SequencerStatus, ShutterState

import config


def generate_image_filepath(tmp_night_folder=None):
    """
    Creates a full filepath including filename. If the destination folder does not exist it is created.

    :return: the generated filepath
    """

    if tmp_night_folder is None:
        tmp_night_folder, _ = create_night_folders()

    filename = f'tmp_KALAO.{kalao_time.get_isotime()}.fits'
    filepath = tmp_night_folder / filename

    return filepath


def create_night_folders():
    # Prepare temporary and science folder
    # check if folder exists
    # remove temporary folder of previous night if empty

    tmp_night_folder = config.FITS.temporary_data_storage / kalao_time.get_start_of_night(
    )
    science_night_folder = config.FITS.science_data_storage / kalao_time.get_start_of_night(
    )

    # Check if tmp and science folders exist
    if not tmp_night_folder.exists(parents=True):
        tmp_night_folder.mkdir()
    if not science_night_folder.exists():
        science_night_folder.mkdir(parents=True)

    # Remove empty folder in tmp except for current night folder
    for folder in config.FITS.temporary_data_storage.iterdir():
        folder = config.FITS.temporary_data_storage / folder

        # Check is folder is empty
        if folder != tmp_night_folder and not any(folder.iterdir()):
            folder.rmdir()

    return tmp_night_folder, science_night_folder


def save_tmp_image(image_path, sequencer_arguments=None):
    '''
    Updates the temporary image header and saves into the archive.

    :param image_path:
    :param sequencer_arguments: argument list received by the sequencer
    :return:
    '''
    science_night_folder = config.FITS.science_data_storage / kalao_time.get_start_of_night(
    )

    # Remove tmp_ from filename
    target_path_name = science_night_folder / image_path.name.replace(
        'tmp_', '')

    if image_path.exists() and science_night_folder.exists():
        update_header(image_path, sequencer_arguments=sequencer_arguments)
        shutil.move(image_path, target_path_name)
        # TODO Remove write permission
        # target_path_name.chmod(file_mask)

        # TODO possibly add the right UID and GID
        database.store(
            'obs', {
                'sequencer_log': f'Saving {image_path} to {target_path_name}',
                'fli_last_image_path': target_path_name
            })

        return target_path_name
    else:
        database.store(
            'obs', {
                'sequencer_log':
                    f'[ERROR] Unable to save {image_path} to {target_path_name}',
                'sequencer_status':
                    SequencerStatus.ERROR
            })

        return -1


def update_db_from_telheader():
    """
    Updates the obs database with the values from the telescope header.

    :return:
    """

    telescope_header_df = _header_from_last_telescope_header()
    if not telescope_header_df.empty:
        data = {}

        # Fill the actual values into the dictionary
        for db_key, keyword in config.FITS.db_from_telheader.items():
            data[db_key] = telescope_header_df.loc[keyword].value

        # Store values in db
        database.store('obs', data)

        return 0

    else:
        return -1


def update_header(image_path, sequencer_arguments=None):
    """
    Updates the image header with values from the observing, monitoring, and telemetry logs.

    :param image_path: path to the image to update
    :param sequencer_arguments: argumetns received by the sequencer
    :return:
    """

    # Reading the fits definitions
    header_df = _header_from_yml(config.FITS.fits_header_file)

    if sequencer_arguments is not None:
        type = sequencer_arguments.get('type')

        if type in config.FITS.base_header:
            for k, v in config.FITS.base_header[type].items():
                header_df.loc[f'HIERARCH ESO {k}'].value = v

    with fits.open(image_path, mode='update') as hdul:
        # Change something in hdul.
        fits_header = hdul[0].header

        if 'DATE-OBS' in fits_header.keys():
            dt = datetime.fromisoformat(fits_header['DATE-OBS']).replace(
                tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(fits_header['DATE']).replace(
                tzinfo=timezone.utc)

        header_df = header_df.concat([
            header_df,
            _header_from_db('obs', dt),
            _header_from_db('monitoring', dt),
            _header_from_db('telemetry', dt),
            _clean_header(_header_from_last_telescope_header())
        ]).query('~index.duplicated(keep="last")')

        header_df = _dynamic_cards_update(header_df,
                                          seq_args=sequencer_arguments)
        header_df = _sort_header(header_df)
        _header_to_fits_header(header_df, fits_header)

        wcs = starfinder.generate_wcs()
        fits_header.update(wcs.to_header())
        hdul.verify('silentfix+warn')

        # Write changes back to original.fits
        hdul.flush()

    return 0


def add_comment(image_path, comment_string):
    with fits.open(image_path, mode='update') as hdul:
        # Change something in hdul.
        header = hdul[0].header
        header.comment = comment_string
        hdul.flush()

    return 0


def get_last_image_path():
    """
    Retrieve the file path of the latest image

    :return: file_path and file_Date
    """
    return _get_image_path('last')


def get_temporary_image_path():
    """
    Retrieve the file path of the latest temporary image

    :return: file_path and file_Date
    """

    return _get_image_path('temporary')


def _get_image_path(image_type):
    if image_type in ['last', 'temporary']:
        last_image = database.get_last('obs', f'fli_{image_type}_image_path')

        if last_image is not None:
            return Path(last_image.get('value')), last_image.get('timestamp')

    return None, None


def _header_empty():
    header_df = pd.DataFrame(columns=['value', 'comment', 'source'])
    header_df.index.name = 'keyword'

    return header_df


def _header_from_fits(file):
    '''
    Reads a fits header and reformats it into a dataframe

    :param header:
    :return: header dataframe
    '''
    fits_header = fits.getheader(file)
    header_dict = {}

    for keyword in fits_header.keys():
        header_dict[keyword] = {
            'value': fits_header[keyword],
            'comment': fits_header.comments[keyword],
            'source': f'fits:{file}'
        }

    header_df = pd.DataFrame.from_dict(header_dict, orient='index')
    header_df.index.name = 'keyword'
    return header_df


def _header_from_yml(file):
    '''
    Reads the fits header file definition YAML file and returns a pandas dataframe with
    the following keys: keyword, value, comment

    :return: pandas dataframe with the fits definitions
    '''

    with open(file, 'r') as f:
        header_df = pd.json_normalize(yaml.safe_load(f))

    header_df.set_index('keyword', inplace=True)
    header_df['source'] = f'yml:{file}'

    return header_df


def _header_from_db(collection_name, dt):
    header_dict = {}
    query_list = {}

    for k, v in database.definitions[collection_name]['metadata'].items():
        fits_keyword = v.get('fits_keyword')
        if fits_keyword is not None:
            # Unit
            unit = v.get("unit")
            if unit is None or unit == '':
                unit = ""
            else:
                unit = f'[{unit}] '
            unit = unit.replace('°', 'deg')

            max_comment_length = config.FITS.max_comment_length - len(unit)

            # Comment
            comment = v.get("fits_comment")
            if comment is None:
                comment = v.get("long")
            if comment is None or len(comment) > max_comment_length:
                comment = v.get("short")

            comment = kalao_string.ellipsis(comment)

            header_dict[fits_keyword] = {
                'value': None,
                'comment': f'{unit}{comment}',
                'source': f'db:{collection_name}:{k}'
            }
            query_list[k] = fits_keyword

    if dt is not None:
        data = database.get(collection_name, query_list.keys(), dt)

        for key, keyword in query_list.items():
            header_dict[keyword].value = data[key]['values'][0]['value']

    header_df = pd.DataFrame.from_dict(header_dict, orient='index')
    header_df.index.name = 'keyword'
    return header_df


def _sort_header(header_df):
    # Search for first HIERARCH keyword (i.e. longer than 8) and split in two header dataframes
    HIERARCH_lines = np.array(
        header_df.index.str.len() > config.FITS.max_length_without_HIERARCH)

    header_head_df = header_df[HIERARCH_lines]
    header_tail_df = header_df[~HIERARCH_lines]

    header_df = pd.concat([header_head_df, header_tail_df.sort_index()])

    return header_df


def _header_to_fits_header(header_df, fits_header):
    # Remove all cards before updating
    # fits_header.clear()

    for keyword, row in header_df.fillna(value='').iterrows():
        fits_header.set(keyword, row.value, row.comment.strip())


def _header_from_last_telescope_header():
    """
    Reads header file path from database base and returns the header content along with the path

    :return:
    """

    tcs_header_path_record = database.get_last('obs', 'tcs_header_path')

    header_age = (kalao_time.now() -
                  tcs_header_path_record['timestamp']).total_seconds()

    if 'home' in tcs_header_path_record['value']:
        tcs_header_path = config.SEQ.T4_root / tcs_header_path_record['value'][
            1:]
    else:
        tcs_header_path = Path(tcs_header_path_record['value'])

    if header_age > config.FITS.tcs_header_validity:
        database.store(
            'obs', {
                'sequencer_log':
                    f'[WARNING] {tcs_header_path_record["value"]} is {header_age / 60} minutes old. Discarding obsolete header'
            })
        return _header_empty()

    elif tcs_header_path.is_file():
        return _header_from_fits(tcs_header_path)

    else:
        database.store('obs', {
            'sequencer_log':
                f'[ERROR] Header file not found: {tcs_header_path}'
        })
        return _header_empty()


def _clean_header(header_df):
    # Remove first part of header
    # TODO set the cutoff keyword in kalao.config
    if 'OBSERVER' in header_df.index:
        max_i = header_df.index.get_loc('OBSERVER')
        drop_list = []
        for i in range(max_i + 1):
            drop_list.append(header_df.index[i])

        header_df = header_df.drop(index=drop_list)

    rename_dict = {}
    for index, row in header_df.iterrows():
        if len(index) <= config.FITS.max_length_without_HIERARCH:
            rename_dict[index] = index.upper()
        else:
            rename_dict[index] = f'HIERARCH {index.upper()}'

    return header_df.rename(index=rename_dict)


def _dynamic_cards_update(header_df, seq_args=None):
    date_obs = header_df.loc['DATE-OBS'].value
    date_end = header_df.loc['DATE-END'].value

    dt_obs = datetime.fromisoformat(date_obs)

    location = euler.observing_location()

    astro_time_obs = Time(date_obs, scale='utc', location=location)
    astro_time_end = Time(date_end, scale='utc', location=location)

    ra = Angle(header_df.loc['RA'].value, unit=u.deg)
    dec = Angle(header_df.loc['DEC'].value, unit=u.deg)

    # Update HIERARCH ESO INS SHUT ST
    shutter = header_df.loc['HIERARCH ESO INS SHUT ST']
    shutter.comment = f'{shutter.comment} ({shutter.value.lower()})'
    if shutter.value == ShutterState.OPEN:
        shutter.value = True
    elif shutter.value == ShutterState.CLOSED:
        shutter.value = False
    else:
        shutter.value = 'ERROR'
    shutter.source += '+dynamic'

    # Update RA
    header_df.loc['RA'].value = ra.deg
    header_df.loc[
        'RA'].comment = f'[deg] {ra.to_string(unit=u.deg, sep=":", precision=1, pad=True)} RA (J2000) pointing'
    header_df.loc['RA'].source += '+dynamic'

    # Update DEC
    header_df.loc['DEC'].value = dec.deg
    header_df.loc[
        'DEC'].comment = f'[deg] {dec.to_string(unit=u.deg, sep=":", precision=1, pad=True)} DEC (J2000) pointing'
    header_df.loc['DEC'].source += '+dynamic'

    # Update MJD-OBS
    header_df.loc['MJD-OBS'].value = astro_time_obs.mjd
    header_df.loc['MJD-OBS'].comment = date_obs
    header_df.loc['MJD-OBS'].source += '+dynamic'

    # Update MJD-END
    header_df.loc['MJD-END'].value = astro_time_end.mjd
    header_df.loc['MJD-END'].comment = date_end
    header_df.loc['MJD-END'].source += '+dynamic'

    # Update UTC
    header_df.loc[
        'UTC'].value = dt_obs.hour * 3600 + dt_obs.minute * 60 + dt_obs.second + dt_obs.microsecond * 10**-6
    header_df.loc[
        'UTC'].comment = f'[s] {dt_obs.time().isoformat(timespec="milliseconds")} UTC'
    header_df.loc['UTC'].source += '+dynamic'

    # Update LST
    header_df.loc['LST'].value = astro_time_obs.sidereal_time(
        'mean').hour * 3600
    header_df.loc[
        'LST'].comment = f"[s] {astro_time_obs.sidereal_time('mean').to_string(u.hour, sep=':', precision=7, pad=True)} LST"
    header_df.loc['LST'].source += '+dynamic'

    # TODO add radecsys value in EQUINOX comment

    if seq_args is not None:
        header_df.loc['HIERARCH ESO OBS TYPE'].value = seq_args.get('type')

    return header_df


def _header_to_string(header_df, max_length=45, float_length=20):
    formatters = {}
    length = {}
    for col in header_df.columns:
        length[col] = header_df[col].astype(str).str.len().max()

        if col == 'value' and length['value'] < float_length:
            length[col] = float_length

        if length[col] > max_length:
            length[col] = max_length

        formatters[col] = eval(
            "lambda x: kalao_string.ellipsis(str(x).ljust(" +
            str(length[col]) + ", ' '), " + str(max_length) + ")")

    float_format = eval("lambda x: f'{x:." + str(float_length - 1) +
                        "g}'.ljust(" + str(length['value']) + ", ' ')")

    pd.set_option("display.colheader_justify", "left")
    return header_df.fillna(
        value='<empty>').to_string(formatters=formatters,
                                   float_format=float_format)


def directory_summary_df(folder):
    """
    Creates a dataframe summarising the header content of all the fits files in a folder.

    :param folder: path to the folder to be summarised
    :return:
    """

    df = None

    for image_filename in folder.rglob("*.fits"):

        print(f'Opening {image_filename}')

        with fits.open(image_filename) as hdul:
            dic = {'filename': image_filename}

            for k in hdul[0].header.cards:
                dic[k[0]] = k[1]

        if df is None:
            df = pd.DataFrame([dic])
        else:
            df = pd.concat([df, pd.DataFrame([dic])], ignore_index=True,
                           axis=0)

    return df


def get_exposure_times(folder, exclude_types=['K_DARK']):
    """
    Get the list of exposure times in the folder pointed at by filepath. By default, DARK exposure times are ignored.

    :param folder: path of the folder to scan.
    :param exclude_types: exposure types to exclude from the scan.
    :return: list of exposure times found.
    """

    directory_summary = directory_summary_df(folder)

    if directory_summary is None:
        exposure_times = []

    else:
        if exclude_types is not None:
            for type_to_exclude in exclude_types:
                # Handle the case where ESO OBS TYPE is undefined in all files
                if 'ESO OBS TYPE' in directory_summary.keys():
                    directory_summary = directory_summary[
                        directory_summary['ESO OBS TYPE'] != type_to_exclude]

        exposure_times = directory_summary['EXPTIME'].unique()

    return exposure_times
