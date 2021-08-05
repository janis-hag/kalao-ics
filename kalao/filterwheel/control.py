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

from microscope.filterwheels import thorlabs
import time

# clear griz, hole
# 0 clear
# 1 jaune g
# 2 violet r
# 3 bleu clair i
# 4 argent z
# 5 empty



def set_position(filter):

    if filter in range(0,6):
        filter_position = filter
    elif filter in:

    fw = thorlabs.ThorlabsFW102C(com='/dev/ttyUSB0')
    fw.enable()
    time.sleep(2)
    fw.initialize()
    time.sleep(2)
    fw.set_position(filter_position)
    time.sleep(6)
    position = fw.get_position()

    if position == filter_position:
        return 0
    else:
        return 1

def get_position():
    fw = thorlabs.ThorlabsFW102C(com='/dev/ttyUSB0')
    fw.enable()
    time.sleep(2)
    fw.initialize()
    time.sleep(2)
    fw.set_position(0)
    time.sleep(6)
    fw.get_position()

    return position


def init():
    fw = thorlabs.ThorlabsFW102C(com='/dev/ttyUSB0')
    fw.enable()
    time.sleep(2)
    fw.initialize()
    time.sleep(2)

    return 0
