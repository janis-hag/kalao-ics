import argparse

import pandas as pd

from kalao.fli import camera
from kalao.utils import file_handling

from kalao.definitions.enums import ReturnCode

import config


def run(args):
    if args.fits is None:
        ret = camera.take_empty('/tmp/fli_empty.fits')

        if ret == ReturnCode.CAMERA_OK:
            fli_header = file_handling._header_from_fits('/tmp/fli_empty.fits')
        else:
            print("[ERROR] Failed to get empty file from FLI camera.")
            fli_header = file_handling._header_empty()
    else:
        fli_header = file_handling._header_from_fits(args.fits)

    df = pd.concat([
        fli_header,
        file_handling._header_from_yml(config.FITS.fits_header_file),
        file_handling._header_from_db('obs', dt=None),
        file_handling._header_from_db('telemetry', dt=None),
        file_handling._header_from_db('monitoring', dt=None),
        #file_handling._clean_header(file_handling._header_from_last_telescope_header()
    ]).query('~index.duplicated(keep="last")')

    df.loc['RA'].value = 0
    df.loc['DEC'].value = 0
    df.loc['HIERARCH ESO INS SHUT ST'].value = 'OPEN'

    df = file_handling._dynamic_cards_update(df, 'K_TRGOBS')
    df = file_handling._sort_header(df)

    print(file_handling._header_to_string(df))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        'Check which keywords will be put in a FITS and where they come from.')
    parser.add_argument('-f', action="store", dest="fits", type=str,
                        default=None,
                        help='FITS file to use as an input (optional)')

    args = parser.parse_args()

    run(args)
