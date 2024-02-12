#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""
import argparse
from pathlib import Path

import numpy as np

from astropy.io import fits

import config


def run(args):
    data = np.genfromtxt(args.input_file)

    flat = np.zeros((12, 12), dtype=np.float32)

    for i in range(0, 10):
        flat[(i+1) // 12, (i+1) % 12] = (data[i] - 0.5) * 3.5

    for i in range(10, 130):
        flat[(i+2) // 12, (i+2) % 12] = (data[i] - 0.5) * 3.5

    for i in range(130, 140):
        flat[(i+3) // 12, (i+3) % 12] = (data[i] - 0.5) * 3.5

    fits.PrimaryHDU(flat).writeto(args.output_file, overwrite=True)

    return 0


if __name__ == '__main__':
    default_output = config.AO.cacao_workdir / 'setupfiles/hwloop/rundir/dmflat_bmc.fits'

    parser = argparse.ArgumentParser(
        description=
        'Convert a flat map from BMC to a fits file compatible with CACAO.')
    parser.add_argument('--input', action="store", dest="input_file",
                        required=True, type=Path, help='Input file (from BMC)')
    parser.add_argument('--output', action="store", dest="output_file",
                        default=default_output, type=Path, help='Output file')

    args = parser.parse_args()

    run(args)
