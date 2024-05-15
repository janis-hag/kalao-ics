import argparse

import pandas as pd

from kalao.utils import file_handling

from kalao.definitions.enums import (FlipMirrorPosition, LaserState,
                                     ObservationType, ShutterState,
                                     TungstenState)

import config

try:
    from kalao.hardware import camera

    camera_imported = True
except ImportError:
    camera_imported = False


def run(args):
    if args.fits is None:
        if camera_imported:
            ret = camera.take_fake('/tmp/camera_fake.fits')

            if ret != None:
                camera_header = file_handling._header_from_fits_file(
                    '/tmp/camera_fake.fits')
            else:
                print("[ERROR] Failed to get empty file from FLI camera.")
                camera_header = file_handling._header_empty()
        else:
            camera_header = file_handling._header_empty()
    else:
        camera_header = file_handling._header_from_fits_file(args.fits)

    df = pd.concat([
        camera_header,
        file_handling._header_from_yml(config.FITS.fits_default_header_file),
        file_handling._header_from_db('obs', dt=None),
        file_handling._header_from_db('telemetry', dt=None),
        file_handling._header_from_db('monitoring', dt=None),
        #file_handling._clean_header(file_handling._header_from_last_telescope_header()
    ]).query('~index.duplicated(keep="last")')

    df.loc['RA', 'value'] = 0
    df.loc['DEC', 'value'] = 0
    df.loc['HIERARCH ESO INS SHUT STATUS', 'value'] = ShutterState.OPEN.value
    df.loc['HIERARCH ESO INS FLIP STATUS',
           'value'] = FlipMirrorPosition.DOWN.value
    df.loc['HIERARCH ESO INS LASER STATUS', 'value'] = LaserState.OFF.value
    df.loc['HIERARCH ESO INS TUNGSTEN STATUS',
           'value'] = TungstenState.OFF.value

    df = file_handling._dynamic_cards_update(
        df, ObservationType.TARGET, True, 'KALAO.1970-01-01T00:00:00.000.fits')
    df = file_handling._sort_header(df)

    print(file_handling._header_to_string(df))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        'Check which keywords will be put in a FITS and where they come from.')
    parser.add_argument('--file', action="store", dest="fits", type=str,
                        default=None,
                        help='FITS file to use as an input (optional)')

    args = parser.parse_args()

    run(args)
