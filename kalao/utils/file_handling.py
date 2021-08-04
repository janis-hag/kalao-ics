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
from kalao.utils import kalao_time

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')

# Read config file and create a dict for each section where keys is parameter
parser = ConfigParser()
parser.read(config_path)

Tmp_folder = parser.get('FLI','TemporaryDataStorage')
Science_folder = parser.get('FLI','ScienceDataStorage')

def create_temporary_folder():
    # Prepare temporary dark folder
    # TODO add night date to folder name
    # check if folder exists

    Tmp_night_folder = Tmp_folder + '/' + kalao_time.get_start_of_night()

    if not os.path.exists(Tmp_night_folder):
        os.mkdir(Tmp_night_folder)

    return Tmp_night_folder

def save_temporary_folder():
    Tmp_night_folder = Tmp_folder + '/' + kalao_time.get_start_of_night()
    Science_night_folder = Science_folder + '/' + kalao_time.get_start_of_night()

    # if tmp folder of the night exist, move it to ScienceDataStorage
    if os.path.exists(Tmp_night_folder):
        os.rename(Tmp_night_folder, Science_night_folder)

    return 0

def clean_temporary_folder():
    for folder in os.listdir(Tmp_folder):
        if os.isdir(folder):
            os.rmdir(Tmp_folder + '/' + folder)
    return 0


def update_header(file):

    return 0
