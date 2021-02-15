#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import numpy
from astropy.io import fits
import sys

if len(sys.argv) != 3:
	print("This script take two args : flat_from_BMC (input) and fits (output)")
	exit()

data = numpy.genfromtxt(sys.argv[1])

flat = numpy.zeros((12, 12))

for i in range(0, 10):
    flat[(i+1) // 12, (i+1) % 12] = (data[i] - 0.5) * 3.5

for i in range(10, 130):
    flat[(i+2) // 12, (i+2) % 12] = (data[i] - 0.5) * 3.5

for i in range(130, 140):
    flat[(i+3) // 12, (i+3) % 12] = (data[i] - 0.5) * 3.5

hdu = fits.PrimaryHDU(flat.astype(numpy.float32))
hdu.writeto(sys.argv[2], overwrite=True)
