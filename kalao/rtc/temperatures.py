#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : temperatures.py
# @Date : 2021-02-24-10-32
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
temperatures.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

import sensors
from kalao.utils import database
from kalao.rtc import gpu_control

def read_all():

    temperatures = {}
    sensors.init()

    try:
        for chip in sensors.iter_detected_chips():
            #print '%s at %s' % (chip, chip.adapter_name)
            for feature in chip:
                #print '  %s: %.2f' % (feature.label, feature.get_value())
                chipname = '_'.join(str(chip).split('-')[:-1])
                sensor_name = chipname + '-' + feature.label
                temperatures[sensor_name.replace(' ', '_')] = feature.get_value()
    finally:
        sensors.cleanup()

    gpu_temp = gpu_control.status()['GPU Current Temp'].split(' ')[0]

    return temperatures


def database_update():
    values = read_all()
    database.store_monitoring(values)