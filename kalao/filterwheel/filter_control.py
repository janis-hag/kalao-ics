#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : control.py
# @Date : 2021-08-02-10-16
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
control.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

import sys
import os
from microscope.filterwheels import thorlabs
import time
from configparser import ConfigParser
from pathlib import Path

# add the necessary path to find the folder kalao for import
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from kalao.utils import database

# clear griz, hole
# 0 clear
# 1 jaune g
# 2 violet r
# 3 bleu clair i
# 4 argent z
# 5 empty

parser = ConfigParser()
config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
parser.read(config_path)

TLFW = parser.get('FLI','ThorlabsFilterWheel')

# Create bidirect dict with filter id (str and int)
Id_filter = parser._sections['FilterPosition']
revd = dict( [reversed(i) for i in Id_filter.items()] )
Id_filter.update(revd)

def create_filter_id():
    return Id_filter

def set_position(filter_arg):

    if type(filter_arg) == int and filter_arg not in range(0,6):
        database.store_obs_log({'filterwheel_log': "Error: wrong filter id got ({})".format(filter_arg)})
        return -1
    elif type(filter_arg) == str:
        if filter_arg not in Id_filter.keys():
            database.store_obs_log({'filterwheel_log': "Error: wrong filter name (got {})".format(filter_arg)})
            return -1
        else:
            filter_arg = Id_filter[filter_arg]

    fw = thorlabs.ThorlabsFilterWheel(com=TLFW)
    fw.enable()
    time.sleep(2)
    fw.initialize()
    time.sleep(2)
    fw.set_position(filter_arg) # Same name of parent func ?
    time.sleep(6)
    position = fw.get_position()

    if position == filter_arg:
        database.store_obs_log({'filterwheel_status': "Filterwheel on {}".format(Id_filter[filter_arg])})
        return 0
    else:
        database.store_obs_log({'filterwheel_log': "Error: filter position expected {}, but got {}".format(filter_arg, position )})
        return -1

def get_position():
    fw = thorlabs.ThorlabsFilterWheel(com=TLFW)
    fw.enable()
    time.sleep(2)
    fw.initialize()
    time.sleep(6)
    fw.get_position()

    return position


def init():

    fw = thorlabs.ThorlabsFilterWheel(com=TLFW)
    fw.enable()
    time.sleep(2)
    fw.initialize()
    time.sleep(2)

    database.store_obs_log({'filterwheel_log': "initialize filerwheel"})

    return 0
