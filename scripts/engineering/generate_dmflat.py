#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import sys

import numpy as np

from astropy.io import fits

if len(sys.argv) != 3:
    print(
        "This script take two args : flat_from_BMC (input) and fits (output)")
    exit()


def run():
    """
    Generate a flat DM map for the Boston MC deformable mirror based on flat provided by BMC.

    :return: exit status
    """
    data = np.genfromtxt(sys.argv[1])

    flat = np.zeros((12, 12), dtype=np.float32)

    for i in range(0, 10):
        flat[(i+1) // 12, (i+1) % 12] = (data[i] - 0.5) * 3.5

    for i in range(10, 130):
        flat[(i+2) // 12, (i+2) % 12] = (data[i] - 0.5) * 3.5

    for i in range(130, 140):
        flat[(i+3) // 12, (i+3) % 12] = (data[i] - 0.5) * 3.5

    fits.PrimaryHDU(flat).writeto(sys.argv[2], overwrite=True)

    return 0


if __name__ == "__main__":
    run()
