import argparse
from pathlib import Path

import numpy as np

from astropy.io import fits

import config


def run(args):
    ##### DM wfsmask

    # yapf: disable
    dm_wfsmask = np.array(
        [[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
         [0., 0., 1., 1., 1., 1., 1., 1., 1., 0., 0., 0., 0., 1., 1., 1., 1., 1., 1., 1., 0., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 0., 0., 0., 1., 1., 1., 0., 0., 1., 1., 1., 0., 0., 0., 1., 1., 1., 0.],
         [0., 1., 1., 1., 0., 0., 0., 1., 1., 1., 0., 0., 1., 1., 1., 0., 0., 0., 1., 1., 1., 0.],
         [0., 1., 1., 1., 0., 0., 0., 1., 1., 1., 0., 0., 1., 1., 1., 0., 0., 0., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 0., 1., 1., 1., 1., 1., 1., 1., 0., 0., 0., 0., 1., 1., 1., 1., 1., 1., 1., 0., 0.],
         [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        ], dtype=np.float32)
    # yapf: enable

    fits.PrimaryHDU(dm_wfsmask).writeto(
        args.output_folder / 'dm/conf/wfsmask.fits', overwrite=True)

    ##### DM dmmask

    # yapf: disable
    dm_dmmask = np.array(
        [[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
         [0., 0., 0., 1., 1., 1., 1., 1., 1., 0., 0., 0.],
         [0., 0., 1., 1., 1., 1., 1., 1., 1., 1., 0., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 0., 0., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 0., 0., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 0., 1., 1., 1., 1., 1., 1., 1., 1., 0., 0.],
         [0., 0., 0., 1., 1., 1., 1., 1., 1., 0., 0., 0.],
         [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        ], dtype=np.float32)
    # yapf: enable

    fits.PrimaryHDU(dm_dmmask).writeto(
        args.output_folder / 'dm/conf/dmmask.fits', overwrite=True)

    ##### TTM wfsmask

    # yapf: disable
    ttm_wfsmask = np.array(
        [[0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
         [0., 0., 0., 1., 1., 1., 1., 1., 1., 0., 0., 0.],
         [0., 0., 1., 1., 1., 1., 1., 1., 1., 1., 0., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 0., 0., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 0., 0., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0.],
         [0., 0., 1., 1., 1., 1., 1., 1., 1., 1., 0., 0.],
         [0., 0., 0., 1., 1., 1., 1., 1., 1., 0., 0., 0.],
         [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        ], dtype=np.float32)
    # yapf: enable

    fits.PrimaryHDU(ttm_wfsmask).writeto(
        args.output_folder / 'ttm/conf/wfsmask.fits', overwrite=True)

    ##### TTM dmmask

    ttm_dmmask = np.array([[1., 1.]], dtype=np.float32)

    fits.PrimaryHDU(ttm_dmmask).writeto(
        args.output_folder / 'ttm/conf/dmmask.fits', overwrite=True)

    ##### TTM wfsrefc

    ttm_wfsrefc = np.zeros((12, 12), dtype=np.float32)

    fits.PrimaryHDU(ttm_wfsrefc).writeto(
        args.output_folder / 'ttm/conf/wfsrefc.fits', overwrite=True)


if __name__ == "__main__":
    default_folder = config.AO.cacao_workdir / 'setupfiles'

    parser = argparse.ArgumentParser(
        description='Generate maks and references fits for CACAO.')
    parser.add_argument('--output', action="store", dest="output_folder",
                        default=default_folder, type=Path,
                        help='Output folder')

    args = parser.parse_args()

    run(args)
