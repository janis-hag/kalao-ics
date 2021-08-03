#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : fits_handling
# @Date : 2021-08-02-11-55
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
file_handling.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

# TODO create functions:
# - def update_fits_header
# - update_temporary_folder( current_folder, temporary_folder)

import sys
import os
from pathlib import Path
import time
from configparser import ConfigParser

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')

# Read config file and create a dict for each section where keys is parameter
parser = ConfigParser()
parser.read(config_path)

Temporary_folder = parser.get('FLI','TemporaryDataStorage')

def create_temporary_folder():
    # Prepare temporary dark folder
    # TODO add night date to folder name
    # check if folder exists
    try:
        for filename in os.listdir(Temporary_folder):
            os.remove(Tempo_dark + "/" + filename)
    except FileNotFoundError:
        os.mkdir(Temporary_folder)

    return Temporary_folder