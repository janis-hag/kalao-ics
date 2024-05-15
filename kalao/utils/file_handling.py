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

import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from astropy import units as u
from astropy.coordinates import Angle, SkyCoord
from astropy.io import fits
from astropy.time import Time

from kalao import database, euler, logger
from kalao.utils import kstring, ktime
from kalao.utils.rprint import rprint

import yaml
from unidecode import unidecode

from kalao.definitions.dataclasses import ROI
from kalao.definitions.enums import (FlipMirrorPosition, LaserState,
                                     ObservationType, ReturnCode, ShutterState,
                                     TungstenState)

import config


def get_tmp_image_filepath() -> Path:
    """
    Creates a full filepath including filename. If the destination folder does not exist it is created.

    :return: the generated filepath
    """

    tmp_night_folder = config.FITS.temporary_data_storage / ktime.get_night_str(
    )

    if not tmp_night_folder.exists():
        tmp_night_folder.mkdir(parents=True)

    # Remove empty folder in tmp except for current night folder
    for folder in config.FITS.temporary_data_storage.iterdir():
        # Check is folder is empty
        if folder != tmp_night_folder and not any(folder.iterdir()):
            folder.rmdir()

    filename = f'tmp_KALAO.{ktime.utc_millis_str()}.fits'
    filepath = tmp_night_folder / filename

    return filepath


def get_focus_sequence_filepath() -> Path:
    """
    Creates a full filepath including filename. If the destination folder does not exist it is created.

    :return: the generated filepath
    """

    focus_folder = config.FITS.focus_data_storage / ktime.get_night_str()

    if not focus_folder.exists():
        focus_folder.mkdir(parents=True)

    filename = f'KALAO.FOCUS.{ktime.utc_millis_str()}.fits'
    filepath = focus_folder / filename

    return filepath


def save_tmp_image(image_path: Path, obs_type: ObservationType,
                   comment: str | None = None) -> Path | None:
    '''
    Updates the temporary image header and saves into the archive.

    :param image_path:
    :param sequencer_arguments: argument list received by the sequencer
    :return:
    '''

    if obs_type == ObservationType.ENGINEERING:
        folder = config.FITS.engineering_data_storage / ktime.get_night_str()
    else:
        folder = config.FITS.science_data_storage / ktime.get_night_str()

    if not folder.exists():
        folder.mkdir(parents=True)

    if image_path.exists():
        final_filename = prepare_final_fits(image_path, obs_type,
                                            comment=comment)
        final_filepath = folder / final_filename

        shutil.move(image_path, final_filepath)
        final_filepath.chmod(config.FITS.file_mask)
        # TODO possibly add the right UID and GID

        database.store('obs', {'camera_last_image_path': final_filepath})
        logger.info('sequencer', f'Saved {image_path} to {final_filepath}')

        symlink = config.FITS.last_image
        symlink.unlink(missing_ok=True)
        symlink.symlink_to(final_filepath)

        symlink = config.FITS.last_image_all
        symlink.unlink(missing_ok=True)
        symlink.symlink_to(final_filepath)

        return final_filepath
    else:
        logger.error('sequencer', f'Unable to save {image_path}.')

        return None


def update_db_from_telheader() -> ReturnCode:
    """
    Updates the obs database with the values from the telescope header.

    :return:
    """

    telescope_header_df = _header_from_last_telescope_header()
    if not telescope_header_df.empty:
        data = {}

        # Fill the actual values into the dictionary
        for db_key, keyword in config.FITS.db_from_telheader.items():
            data[db_key] = telescope_header_df.loc[keyword, 'value']

        # Store values in db
        database.store('obs', data)

        return ReturnCode.OK

    else:
        return ReturnCode.GENERIC_ERROR


def prepare_final_fits(image_path: Path, obs_type: ObservationType,
                       comment: str | None = None) -> str:
    """
    Updates the image header with values from the observing, monitoring, and telemetry logs.

    :param image_path: path to the image to update
    :param sequencer_arguments: argumetns received by the sequencer
    :return:
    """

    # Reading the fits definitions
    header_base = _header_from_yml(config.FITS.fits_default_header_file)

    for key, value in config.FITS.base_header[obs_type].items():
        header_base.loc[f'HIERARCH ESO {key}', 'value'] = value

    with fits.open(image_path, mode='update') as hdul:
        fits_header = hdul[0].header

        dt_obs = datetime.fromisoformat(fits_header['DATE-OBS']).replace(
            tzinfo=timezone.utc)
        filename = f'KALAO.{ktime.utc_millis_str(dt_obs)}.fits'

        header_obs = _header_from_db('obs', dt_obs)
        header_monitoring = _header_from_db('monitoring', dt_obs)
        header_telemetry = _header_from_db('telemetry', dt_obs)

        flipmirror_position = header_monitoring.loc[
            'HIERARCH ESO INS FLIP STATUS', 'value']
        shutter_state = header_monitoring.loc['HIERARCH ESO INS SHUT STATUS',
                                              'value']

        on_sky = obs_type in config.FITS.on_sky_types or (
            obs_type == ObservationType.ENGINEERING and flipmirror_position
            == FlipMirrorPosition.DOWN and shutter_state == ShutterState.OPEN)

        if on_sky:
            header_telescope = _clean_header(
                _header_from_last_telescope_header())
        else:
            header_telescope = _header_empty()

        header_df = pd.concat([
            _header_from_fits_header(fits_header, f'fits:{image_path.name}'),
            header_base,
            header_obs,
            header_monitoring,
            header_telemetry,
            header_telescope,
        ]).query('~index.duplicated(keep="last")')

        header_df = _dynamic_cards_update(header_df, obs_type, on_sky,
                                          filename)
        header_df = _sort_header(header_df)
        _header_to_fits_header(header_df, fits_header)

        if comment is not None:
            fits_header.add_comment(comment)

        hdul.verify('silentfix+warn')

        # Write changes back to original fits
        hdul.flush()

    return filename


def _header_empty() -> pd.DataFrame:
    header_df = pd.DataFrame(columns=['value', 'comment', 'source'])
    header_df.index.name = 'keyword'

    return header_df


def _header_from_fits_file(file: str | Path) -> pd.DataFrame:
    if not isinstance(file, Path):
        file = Path(file)

    fits_header = fits.getheader(file)

    return _header_from_fits_header(fits_header, f'fits:{file.name}')


def _header_from_fits_header(fits_header: fits.Header,
                             source: str) -> pd.DataFrame:
    '''
    Reads a fits header and reformats it into a dataframe

    :param header:
    :return: header dataframe
    '''

    header_dict = {}

    for keyword in fits_header.keys():
        if keyword == 'COMMENT':
            continue

        if len(keyword) > config.FITS.max_length_without_HIERARCH:
            keyword = f'HIERARCH {keyword}'

        header_dict[keyword] = {
            'value': fits_header[keyword],
            'comment': fits_header.comments[keyword],
            'source': f'{source}'
        }

    header_df = pd.DataFrame.from_dict(header_dict, orient='index')
    header_df.index.name = 'keyword'
    return header_df


def _header_from_yml(file: str | Path) -> pd.DataFrame:
    '''
    Reads the fits header file definition YAML file and returns a pandas dataframe with
    the following keys: keyword, value, comment

    :return: pandas dataframe with the fits definitions
    '''

    if not isinstance(file, Path):
        file = Path(file)

    with open(file, 'r') as f:
        header_df = pd.json_normalize(yaml.safe_load(f))

    header_df.set_index('keyword', inplace=True)
    header_df['source'] = f'yml:{file.name}'

    return header_df


def _header_from_db(collection_name: str, dt: datetime | None) -> pd.DataFrame:
    header_dict = {}
    query_list = {}

    for k, v in database.definitions[collection_name]['metadata'].items():
        fits_keyword = v.get('fits_keyword')
        if fits_keyword is not None:
            # Unit
            unit = v.get('unit')
            if unit is None or unit == '':
                unit = ''
            else:
                unit = f'[{unit}] '
            unit = unidecode(unit, errors='strict')

            max_comment_length = config.FITS.max_comment_length - len(unit)

            # Comment
            comment = v.get('fits_comment')
            # if comment is None:
            #     comment = v.get('long')
            if comment is None or len(comment) > max_comment_length:
                comment = v.get('short')

            comment = unidecode(comment, errors='strict')
            comment = kstring.ellipsis(comment, max_comment_length)

            header_dict[fits_keyword] = {
                'value': None,
                'comment': f'{unit}{comment}',
                'source': f'db:{collection_name}:{k}'
            }
            query_list[k] = fits_keyword

    # Note: dt=None is mainly for debugging purposes
    if dt is not None:
        data = database.get(collection_name, query_list.keys(), at=dt)

        for key, keyword in query_list.items():
            if key in data:
                header_dict[keyword]['value'] = data[key][0]['value']

    header_df = pd.DataFrame.from_dict(header_dict, orient='index')
    header_df.index.name = 'keyword'
    return header_df


def _sort_header(header_df: pd.DataFrame) -> pd.DataFrame:
    # Search for first HIERARCH keyword (i.e. longer than 8) and split in two header dataframes
    HIERARCH_lines = np.array(
        header_df.index.str.len() > config.FITS.max_length_without_HIERARCH)

    header_head_df = header_df[~HIERARCH_lines]
    header_tail_df = header_df[HIERARCH_lines]

    header_df = pd.concat([
        header_head_df.sort_index(),
        header_tail_df.sort_index()
    ])

    return header_df


def _header_to_fits_header(header_df: pd.DataFrame,
                           fits_header: fits.Header) -> None:
    # Remove all cards before updating
    # fits_header.clear()

    for keyword, row in header_df.fillna(value='').iterrows():
        fits_header.set(keyword, row.value, row.comment.strip())


def _header_from_last_telescope_header() -> pd.DataFrame:
    """
    Reads header file path from database base and returns the header content along with the path

    :return:
    """

    tcs_header_path_record = database.get_last('obs', 'tcs_header_path')

    header_age = (datetime.now(timezone.utc) -
                  tcs_header_path_record['timestamp']).total_seconds()

    tcs_header_path = Path(tcs_header_path_record['value'])

    if header_age > config.FITS.tcs_header_validity:
        logger.warn(
            'sequencer',
            f'{tcs_header_path_record["value"]} is {header_age / 60} minutes old. Discarding obsolete header.'
        )
        return _header_empty()

    elif tcs_header_path.is_file():
        return _header_from_fits_file(tcs_header_path)

    else:
        logger.error('sequencer', f'Header file not found: {tcs_header_path}')
        return _header_empty()


def _clean_header(header_df: pd.DataFrame) -> pd.DataFrame:
    # # Remove first part of header
    # # TODO set the cutoff keyword in kalao.config
    # if 'OBSERVER' in header_df.index:
    #     max_i = header_df.index.get_loc('OBSERVER')
    #     drop_list = []
    #     for i in range(max_i + 1):
    #         drop_list.append(header_df.index[i])
    #
    #     header_df = header_df.drop(index=drop_list)

    rename_dict = {}
    for index, row in header_df.iterrows():
        if len(index) <= config.FITS.max_length_without_HIERARCH:
            rename_dict[index] = index.upper()
        elif index.startswith('HIERARCH'):
            rename_dict[index] = index.upper()
        else:
            rename_dict[index] = f'HIERARCH {index.upper()}'

    return header_df.rename(index=rename_dict)


def _dynamic_cards_update(header_df: pd.DataFrame, obs_type: ObservationType,
                          on_sky: bool, filename: str) -> pd.DataFrame:
    date_obs = header_df.loc['DATE-OBS', 'value']
    date_end = header_df.loc['DATE-END', 'value']

    dt_obs = datetime.fromisoformat(date_obs).replace(tzinfo=timezone.utc)

    location = euler.observing_location()

    astro_time_obs = Time(date_obs, scale='utc', location=location)
    astro_time_end = Time(date_end, scale='utc', location=location)

    # Update ARCFILE
    header_df.loc['ARCFILE', 'value'] = filename
    header_df.loc['ARCFILE', 'source'] += '+dynamic'

    # Update HIERARCH ESO INS SOFW ID
    header_df.loc['HIERARCH ESO INS SOFW ID',
                  'value'] = f'KALAO-ICS/{config.version}'
    header_df.loc['HIERARCH ESO INS SOFW ID', 'source'] += '+dynamic'

    # Update HIERARCH ESO TPL ID
    header_df.loc['HIERARCH ESO TPL ID', 'value'] = str(obs_type)
    header_df.loc['HIERARCH ESO TPL ID', 'source'] += '+dynamic'

    # Create HIERARCH ESO INS SHUT ST
    shutter = header_df.loc['HIERARCH ESO INS SHUT STATUS']
    header_df.loc['HIERARCH ESO INS SHUT ST'] = (
        shutter.value == ShutterState.OPEN, shutter.comment, 'dynamic')

    # Create HIERARCH ESO INS SHUT ST
    flipmirror = header_df.loc['HIERARCH ESO INS FLIP STATUS']
    header_df.loc['HIERARCH ESO INS FLIP ST'] = (
        flipmirror.value == FlipMirrorPosition.UP, flipmirror.comment,
        'dynamic')

    # Create HIERARCH ESO INS LASER ST
    laser = header_df.loc['HIERARCH ESO INS LASER STATUS']
    header_df.loc['HIERARCH ESO INS LASER ST'] = (laser.value == LaserState.ON,
                                                  laser.comment, 'dynamic')

    # Create HIERARCH ESO INS TUNGSTEN ST
    tungsten = header_df.loc['HIERARCH ESO INS TUNGSTEN STATUS']
    header_df.loc['HIERARCH ESO INS TUNGSTEN ST'] = (
        tungsten.value == TungstenState.ON, tungsten.comment, 'dynamic')

    # Update MJD-OBS
    header_df.loc['MJD-OBS', 'value'] = round(astro_time_obs.mjd, 8)
    header_df.loc['MJD-OBS', 'comment'] = date_obs
    header_df.loc['MJD-OBS', 'source'] += '+dynamic'

    # Update MJD-END
    header_df.loc['MJD-END', 'value'] = round(astro_time_end.mjd, 8)
    header_df.loc['MJD-END', 'comment'] = date_end
    header_df.loc['MJD-END', 'source'] += '+dynamic'

    # Update UTC
    header_df.loc['UTC', 'value'] = round(
        dt_obs.hour * 3600 + dt_obs.minute * 60 + dt_obs.second +
        dt_obs.microsecond * 10**-6, 3)
    header_df.loc[
        'UTC',
        'comment'] = f'[s] {dt_obs.time().isoformat(timespec="milliseconds")} UTC'
    header_df.loc['UTC', 'source'] += '+dynamic'

    # Update LST
    header_df.loc['LST', 'value'] = round(
        astro_time_obs.sidereal_time('mean').hour * 3600, 3)
    header_df.loc[
        'LST',
        'comment'] = f"[s] {astro_time_obs.sidereal_time('mean').to_string(u.hour, sep=':', precision=3, pad=True)} LST"
    header_df.loc['LST', 'source'] += '+dynamic'

    if on_sky:
        ra = Angle(header_df.loc['RA', 'value'], unit=u.deg)
        dec = Angle(header_df.loc['DEC', 'value'], unit=u.deg)

        # Update RA
        header_df.loc['RA', 'value'] = ra.deg
        header_df.loc[
            'RA',
            'comment'] = f'[deg] {ra.to_string(unit=u.deg, sep=":", precision=1, pad=True)} RA (J2000) pointing'
        header_df.loc['RA', 'source'] += '+dynamic'

        # Update DEC
        header_df.loc['DEC', 'value'] = dec.deg
        header_df.loc[
            'DEC',
            'comment'] = f'[deg] {dec.to_string(unit=u.deg, sep=":", precision=1, pad=True)} DEC (J2000) pointing'
        header_df.loc['DEC', 'source'] += '+dynamic'

        coord = SkyCoord(ra=ra, dec=dec, frame=config.Euler.frame,
                         equinox=config.Euler.equinox)

        header_df.loc['OBJECT',
                      'value'] = header_df.loc['HIERARCH ESO OBS TARG NAME',
                                               'value']
        header_df.loc['OBJECT', 'source'] += '+dynamic'
    else:
        header_df.drop('RA', inplace=True)
        header_df.drop('DEC', inplace=True)

        header_df.loc['OBJECT',
                      'value'] = header_df.loc['HIERARCH ESO DPR TYPE',
                                               'value']
        header_df.loc['OBJECT', 'source'] += '+dynamic'

        coord = None

    roi = ROI(header_df.loc['HIERARCH ESO DET WIN1 STRX', 'value'] - 1 -
              header_df.loc['HIERARCH ESO DET OUT1 PRSCX', 'value'],
              header_df.loc['HIERARCH ESO DET WIN1 STRY', 'value'] - 1 -
              header_df.loc['HIERARCH ESO DET OUT1 PRSCY', 'value'],
              header_df.loc['HIERARCH ESO DET WIN1 NX', 'value'],
              header_df.loc['HIERARCH ESO DET WIN1 NY',
                            'value'])  # Note: FITS indexing starts at 1

    header_wcs = generate_wcs(coord, astro_time_obs, roi=roi)

    return pd.concat([header_wcs, header_df])


def _header_to_string(header_df: pd.DataFrame, max_length: int = 45,
                      float_length: int = 20) -> str:
    formatters = {}
    length = {}
    for col in header_df.columns:
        length[col] = header_df[col].astype(str).str.len().max()

        if col == 'value' and length['value'] < float_length:
            length[col] = float_length

        if length[col] > max_length:
            length[col] = max_length

        formatters[col] = lambda _, length=length[col]: kstring.ellipsis(
            str(_).ljust(length, ' '), max_length)

        float_format = lambda _: f'{_:.{float_length}f}'[0:float_length].ljust(
            length['value'], ' ')

    pd.set_option("display.colheader_justify", "left")
    return header_df.fillna(
        value='<empty>').to_string(formatters=formatters,
                                   float_format=float_format)


def generate_wcs(coord: SkyCoord, time: Time,
                 roi: ROI | None = None) -> pd.DataFrame:
    """
    Queries the current telescope coordinates to generate a WCS object.

    :return: WCS object with current telescope coordinates
    """

    if roi is None:
        center_x = config.Camera.center_x
        center_y = config.Camera.center_y
    else:
        center_x = config.Camera.center_x - roi.x
        center_y = config.Camera.center_y - roi.y

    wcs_header = _header_empty()

    wcs_header.loc['WCSAXES'] = (2, 'Number of coordinate axes', 'wcs')

    wcs_header.loc['CRPIX1'] = (center_x + 1,
                                'Pixel coordinate of reference point', 'wcs'
                                )  # Note: FITS indexing starts at 1
    wcs_header.loc['CRPIX2'] = (center_y + 1,
                                'Pixel coordinate of reference point', 'wcs'
                                )  # Note: FITS indexing starts at 1

    if coord is not None:
        parang = parallactic_angle(coord, time) * np.pi / 180
        parang = 0  # TODO: remove

        sx = config.Camera.plate_scale / 3600
        sy = config.Camera.plate_scale / 3600
        cos = np.cos(parang)
        sin = np.sin(parang)

        transformation_matrix = np.array([[sx * cos, -sy * sin],
                                          [sx * sin, sy * cos]])

        wcs_header.loc['CTYPE1'] = ('RA---TAN',
                                    'Right ascension, gnomonic projection',
                                    'wcs')
        wcs_header.loc['CTYPE2'] = ('DEC--TAN',
                                    'Declination, gnomonic projection', 'wcs')

        wcs_header.loc['CRVAL1'] = (
            coord.ra.degree, '[deg] Coordinate value at reference point',
            'wcs')
        wcs_header.loc['CRVAL2'] = (
            coord.dec.degree, '[deg] Coordinate value at reference point',
            'wcs')

        wcs_header.loc['CUNIT1'] = ('deg',
                                    'Units of coordinate increment and value',
                                    'wcs')
        wcs_header.loc['CUNIT2'] = ('deg',
                                    'Units of coordinate increment and value',
                                    'wcs')

        wcs_header.loc['CD1_1'] = (transformation_matrix[0, 0],
                                   'Coordinate transformation matrix element',
                                   'wcs')
        wcs_header.loc['CD1_2'] = (transformation_matrix[0, 1],
                                   'Coordinate transformation matrix element',
                                   'wcs')
        wcs_header.loc['CD2_1'] = (transformation_matrix[1, 0],
                                   'Coordinate transformation matrix element',
                                   'wcs')
        wcs_header.loc['CD2_2'] = (transformation_matrix[1, 1],
                                   'Coordinate transformation matrix element',
                                   'wcs')

        radesys = coord.frame.name.upper()

        wcs_header.loc['RADESYS'] = (radesys, 'Equatorial coordinate system',
                                     'wcs')

        if radesys != 'ICRS':
            wcs_header.loc['EQUINOX'] = (
                coord.equinox.jyear, '[yr] Equinox of equatorial coordinates',
                'wcs')

    return wcs_header


def parallactic_angle(coord: SkyCoord, time: Time) -> float:
    r2d = 180 / np.pi
    d2r = np.pi / 180

    geolat_rad = config.Euler.latitude * d2r

    lst_ra = time.sidereal_time('mean').hour * 15 * d2r  #(15./3600)*d2r

    ha_rad = lst_ra - coord.ra.rad
    dec_rad = coord.dec.rad

    # VLT TCS formula
    f1 = float(np.cos(geolat_rad) * np.sin(ha_rad))
    f2 = float(
        np.sin(geolat_rad) * np.cos(dec_rad) -
        np.cos(geolat_rad) * np.sin(dec_rad) * np.cos(ha_rad))
    parang = -r2d * np.arctan2(-f1, f2)  # Sign depends on focus

    return parang


def directory_summary_df(folder: Path) -> pd.DataFrame:
    """
    Creates a dataframe summarising the header content of all the fits files in a folder.

    :param folder: path to the folder to be summarised
    :return:
    """

    df = None

    for image_filename in folder.rglob("*.fits"):

        rprint(f'Opening {image_filename}')

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


def get_exposure_times(
    folder: Path | None = None,
    exclude_types: list[ObservationType] = [ObservationType.DARK
                                            ]) -> list[float]:
    """
    Get the list of exposure times in the folder pointed at by filepath. By default, DARK exposure times are ignored.

    :param folder: path of the folder to scan.
    :param exclude_types: exposure types to exclude from the scan.
    :return: list of exposure times found.
    """

    if folder is None:
        folder = config.FITS.science_data_storage / ktime.get_night_str()

    if not folder.exists():
        return []

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
