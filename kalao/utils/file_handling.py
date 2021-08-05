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

def create_night_folder():
    # Prepare temporary and science folder
    # check if folder exists
    # remove temporary folder of previous night if empty

    Tmp_night_folder = Tmp_folder+os.sep+kalao_time.get_start_of_night()
    Science_night_folder = Science_folder+os.sep+kalao_time.get_start_of_night()

    if not os.path.exists(Tmp_night_folder):
        os.mkdir(Tmp_night_folder)
    if not os.path.exists(Science_night_folder):
        os.mkdir(Science_night_folder)

    for folder in os.listdir(Tmp_folder):
        tmp_path = os.path.abspath(folder)
        if tmp_path != Tmp_night_folder and len(os.listdir(tmp_path)) == 0:
            os.rmdir(tmp_path)

    return Tmp_night_folder

def save_tmp_picture(image_path):
    Science_night_folder = Science_folder+os.sep+kalao_time.get_start_of_night()

    if os.path.exists(image_path) and os.path.exists(Science_night_folder):
        os.rename(image_path, Science_night_folder+os.sep+os.path.basename(image_path))
        return 0
    else:
        return 1

def update_header(image_path):

    return 0
