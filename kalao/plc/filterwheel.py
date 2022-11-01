#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : camera.py
# @Date : 2021-08-02-10-16
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
camera.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

import os
import sys
import time
from configparser import ConfigParser
from pathlib import Path

from microscope.filterwheels import thorlabs

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

DEVICEPORT = parser.get('FilterWheel','DevicePort')
ENABLEWAIT = parser.getfloat('FilterWheel','EnableWait')
INITIALIZATIONWAIT = parser.getfloat('FilterWheel','InitializationWait')
POSITIONCHANGEWAIT = parser.getfloat('FilterWheel','PositionChangeWait')

# Create bidirect dict with filter id (str and int)
# Id_filter = parser._sections['FilterPosition']
# revd = dict( [reversed(i) for i in Id_filter.items()] )
# Id_filter.update(revd)

Id_filter_dict = {}
for key, val in parser.items( 'FilterPosition'):
    Id_filter_dict[key] = int(val)
    Id_filter_dict[int(val)] = key


def create_filter_id():
    return Id_filter_dict


def set_position(filter_arg):

    if type(filter_arg) == int and filter_arg not in range(0,6):
        database.store_obs_log({'filterwheel_log': "Error: wrong filter id got ({})".format(filter_arg)})
        return -1
    elif type(filter_arg) == str:
        filter_arg = filter_arg.lower()
        if filter_arg not in Id_filter_dict.keys():
            database.store_obs_log({'filterwheel_log': "Error: wrong filter name (got {})".format(filter_arg)})
            return -1
        else:
            filter_arg = Id_filter_dict[filter_arg]

    fw = thorlabs.ThorlabsFilterWheel(com=DEVICEPORT)
    # fw.enable()
    # time.sleep(ENABLEWAIT)
    # fw.initialize()
    # time.sleep(INITIALIZATIONWAIT)
    fw.set_position(filter_arg) # Same name of parent func ?
    time.sleep(POSITIONCHANGEWAIT)
    position = fw.get_position()
    filter_name = Id_filter_dict[position]

    if position == filter_arg:
        database.store_obs_log({'filterwheel_status': "Filterwheel on {}".format(Id_filter_dict[filter_arg])})
        return position, filter_name
    else:
        database.store_obs_log({
            'filterwheel_log': "Error: filter position expected {}, but got {}".format(filter_arg, position)})
        return -1


def get_position():
    fw = thorlabs.ThorlabsFilterWheel(com=DEVICEPORT)
    # fw.enable()
    # time.sleep(ENABLEWAIT)
    # fw.initialize()
    # time.sleep(INITIALIZATIONWAIT)
    position = fw.get_position()
    filter_name = Id_filter_dict[position]

    return position, filter_name


def init():

    fw = thorlabs.ThorlabsFilterWheel(com=DEVICEPORT)
    fw.enable()
    time.sleep(ENABLEWAIT)
    fw.initialize()
    time.sleep(INITIALIZATIONWAIT)

    database.store_obs_log({'filterwheel_log': "Initialising filterwheel"})

    return 0
