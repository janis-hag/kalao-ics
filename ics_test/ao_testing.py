#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : ao_testing.py
# @Date : 2022-03-01-10-58
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
ao_testing.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

import subprocess
from subprocess import PIPE, STDOUT
import os
import shutil
import time
import sys

from CacaoProcessTools import fps, FPS_status


def launch_turbulence(refresh=1000, turbulence_file='cube12_12_60000_v10mps_1ms_clean.fits'):

    milk_input = f"""
    loadfits "{turbulence_file}" imc
    readshmim dm01disp04
    streamburst imc dm01disp04 {refresh}
    exitCLI
    """

    cp = subprocess.run(["milk"], input=milk_input, encoding='utf8', stdout=PIPE, stderr=STDOUT)

    print("=========================== STDOUT")

    print(cp.stdout)

    print("=========================== STDERR")

    print(cp.stderr)
