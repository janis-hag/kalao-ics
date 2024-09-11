#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : fits_handling
# @Date : 2021-08-02-11-55
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
fits_handling.py is part of the KalAO Instrument Control Software
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

import yaml
from unidecode import unidecode

from kalao.common import database_definitions, kstring, ktime
from kalao.common.dataclasses import ROI, Template
from kalao.common.enums import (FlipMirrorStatus, LaserStatus, ReturnCode,
                                ShutterStatus, TemplateID, TungstenStatus)

from kalao.ics import database, euler, logger
from kalao.ics.timers import monitoring

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


def save_image(image_path: Path, template: Template,
               comment: str) -> Path | None:
    '''
    Updates the temporary image header and saves into the archive.

    :param image_path:
    :param sequencer_arguments: argument list received by the sequencer
    :return:
    '''

    if template.id == TemplateID.SELF_TEST:
        folder = Path('/tmp')
    elif template.id == TemplateID.ENGINEERING:
        folder = config.FITS.engineering_data_storage / ktime.get_night_str()
    else:
        folder = config.FITS.science_data_storage / ktime.get_night_str()

    if not folder.exists():
        folder.mkdir(parents=True)

    if image_path.exists():
        final_filename = prepare_final_fits(image_path, template,
                                            comment=comment)
        final_filepath = folder / final_filename

        shutil.move(image_path, final_filepath)
        final_filepath.chmod(config.FITS.file_mask)
        # TODO possibly add the right UID and GID

        if template.id != TemplateID.SELF_TEST:
            database.store('obs', {'camera_image_path': final_filepath})

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


def update_db_from_fits(header_df: pd.DataFrame) -> ReturnCode:
    # Version

    version = header_df.loc['HIERARCH ESO DET SOFW ID', 'value']

    if '-dirty' in version:
        logger.warn(
            'sequencer',
            f'Camera software (version {version}) contains uncommited changes')

    # Image sequencial number

    image_number = header_df.loc['HIERARCH ESO DET FRAM ID', 'value']

    previous_number = database.get_last_value(
        'obs', 'camera_image_sequential_number')
    if previous_number is None:
        previous_number = 0

    if image_number <= previous_number:
        logger.warn(
            'sequencer',
            f'Image sequential number from FITS file ({image_number}) lower than or equal to last record ({previous_number})'
        )

    database.store('obs', {'camera_image_sequential_number': image_number})

    return ReturnCode.OK


def prepare_final_fits(image_path: Path, template: Template,
                       comment: str | None = None) -> str:
    """
    Updates the image header with values from the observing, monitoring, and telemetry logs.

    :param image_path: path to the image to update
    :param sequencer_arguments: argumetns received by the sequencer
    :return:
    """

    # Reading the fits definitions
    header_base = _header_from_yaml(config.FITS.fits_default_header_file)

    for key, value in config.FITS.base_header[template.id].items():
        header_base.loc[key, 'value'] = value

    with fits.open(image_path, mode='update') as hdul:
        fits_header = hdul[0].header

        dt_obs = datetime.fromisoformat(fits_header['DATE-OBS']).replace(
            tzinfo=timezone.utc)
        dt_end = datetime.fromisoformat(fits_header['DATE-END']).replace(
            tzinfo=timezone.utc)
        filename = f'KALAO.{ktime.utc_millis_str(dt_obs)}.fits'

        data = monitoring.gather_general() | monitoring.gather_ao()

        header_obs = _header_from_db('obs', dt_end)
        header_monitoring = _header_from_db('monitoring', dt=None, data=data)

        on_sky = template.id in config.FITS.on_sky_templates or (
            template.id == TemplateID.ENGINEERING and
            data['flipmirror_status'] == FlipMirrorStatus.DOWN and
            data['shutter_status'] == ShutterStatus.OPEN)

        if on_sky:
            header_telescope = _clean_header(
                _header_from_last_telescope_header())
        else:
            header_telescope = _header_empty()

        header_fits = _header_from_fits_header(fits_header,
                                               f'fits:{image_path.name}')

        if template.id != TemplateID.SELF_TEST:
            update_db_from_fits(header_fits)

        header_df = pd.concat([
            header_fits,
            header_base,
            header_obs,
            header_monitoring,
            header_telescope,
        ]).query('~index.duplicated(keep="last")')

        header_df = _dynamic_cards_update(header_df, template, on_sky,
                                          filename)
        header_df = _sort_and_clean_header(header_df)
        _header_to_fits_header(header_df, fits_header)

        if comment is not None and comment != '':
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


def _header_from_yaml(file: str | Path) -> pd.DataFrame:
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


def _header_from_db(collection_name: str, dt: datetime | None,
                    data: dict | None = None) -> pd.DataFrame:
    header_dict = {}
    query_list = {}

    for k, v in getattr(database_definitions, collection_name).items():
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
        data = database.get_all_last(collection_name, keys=query_list.keys(),
                                     at=dt)

        for key, keyword in query_list.items():
            if key in data:
                header_dict[keyword]['value'] = data[key]['value']
    elif data is not None:
        for key, keyword in query_list.items():
            if key in data:
                header_dict[keyword]['value'] = data[key]

    header_df = pd.DataFrame.from_dict(header_dict, orient='index')
    header_df.index.name = 'keyword'
    return header_df


def _sort_and_clean_header(header_df: pd.DataFrame) -> pd.DataFrame:
    # Search for first HIERARCH keyword (i.e. longer than 8) and split in two header dataframes
    HIERARCH_lines = np.array(
        header_df.index.str.len() > config.FITS.max_length_without_HIERARCH)

    header_head_df = header_df[~HIERARCH_lines]
    header_tail_df = header_df[HIERARCH_lines]

    header_df = pd.concat([
        header_head_df.sort_index(),
        header_tail_df.sort_index()
    ])

    return header_df.dropna(subset=['value'])


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

    if tcs_header_path_record['value'] is None:
        logger.error('sequencer', 'No TCS header file record in database')
        return _header_empty()

    header_age = (datetime.now(timezone.utc) -
                  tcs_header_path_record['timestamp']).total_seconds()

    tcs_header_path = Path(tcs_header_path_record['value'])

    if header_age > config.FITS.tcs_header_validity:
        logger.warn(
            'sequencer',
            f'{tcs_header_path_record["value"]} is {header_age / 60:.1f} minutes old. Discarding obsolete TCS header.'
        )
        return _header_empty()

    elif tcs_header_path.is_file():
        return _header_from_fits_file(tcs_header_path)

    else:
        logger.error('sequencer',
                     f'TCS header file not found: {tcs_header_path}')
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


def _dynamic_cards_update(header_df: pd.DataFrame, template: Template,
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

    if template.observation_block is not None:
        # Update HIERARCH ESO OBS TPLNO
        header_df.loc['HIERARCH ESO OBS TPLNO',
                      'value'] = template.observation_block.tplno
        header_df.loc['HIERARCH ESO OBS TPLNO', 'source'] += '+dynamic'

    # Update HIERARCH ESO TPL ID
    header_df.loc['HIERARCH ESO TPL ID', 'value'] = str(template.id)
    header_df.loc['HIERARCH ESO TPL ID', 'source'] += '+dynamic'

    # Update HIERARCH ESO TPL START
    header_df.loc['HIERARCH ESO TPL START',
                  'value'] = ktime.utc_millis_str(template.start)
    header_df.loc['HIERARCH ESO TPL START', 'source'] += '+dynamic'

    # Update HIERARCH ESO TPL NEXP
    if template.nexp != -1:
        header_df.loc['HIERARCH ESO TPL NEXP', 'value'] = template.nexp
        header_df.loc['HIERARCH ESO TPL NEXP', 'source'] += '+dynamic'

    # Update HIERARCH ESO TPL EXPNO
    header_df.loc['HIERARCH ESO TPL EXPNO', 'value'] = template.expno
    header_df.loc['HIERARCH ESO TPL EXPNO', 'source'] += '+dynamic'

    # Create HIERARCH ESO INS SHUT ST
    shutter = header_df.loc['HIERARCH ESO INS SHUT STATUS']
    header_df.loc['HIERARCH ESO INS SHUT ST'] = (
        shutter.value == ShutterStatus.OPEN, shutter.comment, 'dynamic')

    # Create HIERARCH ESO INS SHUT ST
    flipmirror = header_df.loc['HIERARCH ESO INS FLIP STATUS']
    header_df.loc['HIERARCH ESO INS FLIP ST'] = (
        flipmirror.value == FlipMirrorStatus.UP, flipmirror.comment, 'dynamic')

    # Create HIERARCH ESO INS LASER ST
    laser = header_df.loc['HIERARCH ESO INS LASER STATUS']
    header_df.loc['HIERARCH ESO INS LASER ST'] = (
        laser.value == LaserStatus.ON, laser.comment, 'dynamic')

    # Create HIERARCH ESO INS TUNGSTEN ST
    tungsten = header_df.loc['HIERARCH ESO INS TUNGSTEN STATUS']
    header_df.loc['HIERARCH ESO INS TUNGSTEN ST'] = (
        tungsten.value == TungstenStatus.ON, tungsten.comment, 'dynamic')

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
        header_df.drop('HIERARCH ESO OBS TARG NAME', inplace=True)

        header_df.loc['OBJECT',
                      'value'] = header_df.loc['HIERARCH ESO DPR TYPE',
                                               'value']
        header_df.loc['OBJECT', 'source'] += '+dynamic'

        coord = None

    roi = ROI(x=header_df.loc['HIERARCH ESO DET WIN1 STRX', 'value'] - 1 -
              header_df.loc['HIERARCH ESO DET OUT1 PRSCX', 'value'],
              y=header_df.loc['HIERARCH ESO DET WIN1 STRY', 'value'] - 1 -
              header_df.loc['HIERARCH ESO DET OUT1 PRSCY', 'value'],
              width=header_df.loc['HIERARCH ESO DET WIN1 NX', 'value'],
              height=header_df.loc['HIERARCH ESO DET WIN1 NY',
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

        def float_format(f):
            return f'{f:.{float_length}f}'[0:float_length].ljust(
                length['value'], ' ')

    pd.set_option('display.colheader_justify', 'left')
    return header_df.fillna(
        value='<empty>').to_string(formatters=formatters,
                                   float_format=float_format)


def generate_wcs(coord: SkyCoord, time: Time, roi: ROI | None = None,
                 method='CD') -> pd.DataFrame:
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
        cdelt1 = config.Camera.plate_scale / 3600
        cdelt2 = config.Camera.plate_scale / 3600
        crota2 = parallactic_angle(
            coord, time) + 90  # + TODO: some offset + mirroring
        crota2_rad = crota2 * np.pi / 180

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

        if method == 'CD':
            cd11 = cdelt1 * np.cos(crota2_rad)
            cd12 = -cdelt1 * np.sin(crota2_rad)
            cd21 = cdelt2 * np.sin(crota2_rad)
            cd22 = cdelt2 * np.cos(crota2_rad)

            wcs_header.loc['CD1_1'] = (
                cd11, 'Coordinate transformation matrix element', 'wcs')
            wcs_header.loc['CD1_2'] = (
                cd12, 'Coordinate transformation matrix element', 'wcs')
            wcs_header.loc['CD2_1'] = (
                cd21, 'Coordinate transformation matrix element', 'wcs')
            wcs_header.loc['CD2_2'] = (
                cd22, 'Coordinate transformation matrix element', 'wcs')

        elif method == 'PC':
            pc11 = np.cos(crota2_rad)
            pc12 = -np.sin(crota2_rad)
            pc21 = np.sin(crota2_rad)
            pc22 = np.cos(crota2_rad)

            wcs_header.loc['CDELT1'] = (cdelt1, 'Coordinate scales', 'wcs')
            wcs_header.loc['CDELT2'] = (cdelt2, 'Coordinate scalse', 'wcs')
            wcs_header.loc['PC1_1'] = (
                pc11, 'Coordinate transformation matrix element', 'wcs')
            wcs_header.loc['PC1_2'] = (
                pc12, 'Coordinate transformation matrix element', 'wcs')
            wcs_header.loc['PC2_1'] = (
                pc21, 'Coordinate transformation matrix element', 'wcs')
            wcs_header.loc['PC2_2'] = (
                pc22, 'Coordinate transformation matrix element', 'wcs')

        elif method == 'CROTA':
            wcs_header.loc['CDELT1'] = (cdelt1, 'Coordinate scales', 'wcs')
            wcs_header.loc['CDELT2'] = (cdelt2, 'Coordinate scales', 'wcs')
            wcs_header.loc['CROTA2'] = (crota2, 'Rotation of coordinate axis',
                                        'wcs')

        else:
            raise ValueError(f'Unknown WCS method {method}')

        radesys = coord.frame.name.upper()

        wcs_header.loc['RADESYS'] = (radesys, 'Equatorial coordinate system',
                                     'wcs')

        if radesys != 'ICRS':
            wcs_header.loc['EQUINOX'] = (
                coord.equinox.jyear, '[yr] Equinox of equatorial coordinates',
                'wcs')

    return wcs_header


def parallactic_angle(coord: SkyCoord, time: Time) -> float:
    lat = euler.observing_location().lat.rad
    lst = time.sidereal_time('apparent').rad
    ha = lst - coord.ra.rad
    dec = coord.dec.rad

    tan1 = np.sin(ha) * np.cos(lat)
    tan2 = np.cos(dec) * np.sin(lat) - np.sin(dec) * np.cos(lat) * np.cos(ha)

    return np.arctan2(tan1, tan2) * 180 / np.pi


def get_exposure_times_for_darks() -> list[float]:
    folder = config.FITS.science_data_storage / ktime.get_night_str()

    if not folder.exists():
        return []

    exposure_times = []
    for filename in folder.rglob('*.fits'):
        header = fits.getheader(filename)

        if header[
                'ESO DPR TYPE'] in config.Calib.Darks.include_types and header[
                    'EXPTIME'] not in exposure_times:
            exposure_times.append(header['EXPTIME'])

    return sorted(exposure_times)
