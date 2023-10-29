#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : inject_turbulences.py
# @Date : 2022-03-01-10-58
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
inject_turbulences.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import subprocess
from subprocess import PIPE, STDOUT

input_fits = "cube12_12_60000_v10mps_1ms.fits"
rate = 1000 # fps

input = f"""
loadfits "{input_fits}" turbulences_cube
readshmim dm01disp04
streamburst turbulences_cube dm01disp04 {rate}
exitCLI
"""

cp = subprocess.run(["milk"], input=input, encoding='utf8', stdout=PIPE,
                    stderr=STDOUT)

print("=========================== STDOUT")

print(cp.stdout)

print("=========================== STDERR")

print(cp.stderr)
