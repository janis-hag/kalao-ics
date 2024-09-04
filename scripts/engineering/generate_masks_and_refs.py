import argparse
from pathlib import Path

import numpy as np

from astropy.io import fits

from kalao.common import ktools

import config


def run(args):
    ##### DM flat

    dm_flat = np.zeros((12, 12), dtype=np.float32)

    fits.PrimaryHDU(dm_flat).writeto(
        args.output_folder / 'hwloop/rundir/dmflat_empty.fits', overwrite=True)

    ##### DM wfsmask

    dm_wfsmask = ktools.generate_dm_wfsmask()

    fits.PrimaryHDU(dm_wfsmask).writeto(
        args.output_folder / 'dmloop/conf/wfsmask.fits', overwrite=True)

    ##### DM dmmask

    dm_dmmask = ktools.generate_dm_dmmask()

    fits.PrimaryHDU(dm_dmmask).writeto(
        args.output_folder / 'dmloop/conf/dmmask.fits', overwrite=True)

    ##### TTM wfsmask

    ttm_wfsmask = ktools.generate_ttm_wfsmask()

    fits.PrimaryHDU(ttm_wfsmask).writeto(
        args.output_folder / 'ttmloop/conf/wfsmask.fits', overwrite=True)

    ##### TTM dmmask

    ttm_dmmask = ktools.generate_ttm_dmmask()

    fits.PrimaryHDU(ttm_dmmask).writeto(
        args.output_folder / 'ttmloop/conf/dmmask.fits', overwrite=True)

    ##### TTM wfsrefc

    ttm_wfsrefc = ktools.generate_ttm_wfsrefc()

    fits.PrimaryHDU(ttm_wfsrefc).writeto(
        args.output_folder / 'ttmloop/conf/wfsrefc.fits', overwrite=True)


if __name__ == '__main__':
    default_folder = config.AO.cacao_workdir / 'setupfiles'

    parser = argparse.ArgumentParser(
        description='Generate maks and references fits for CACAO.')
    parser.add_argument('--output', action="store", dest="output_folder",
                        default=default_folder, type=Path,
                        help='Output folder')

    args = parser.parse_args()

    run(args)
