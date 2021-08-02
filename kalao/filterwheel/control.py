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

def g():
    # move to filter g

def r():
    # move to filter r

fw = thorlabs.ThorlabsFW102C(com='/dev/ttyUSB0')
fw.enable()
time.sleep(2)
fw.initialize()
time.sleep(2)
fw.set_position(0)
time.sleep(6)
fw.get_position()