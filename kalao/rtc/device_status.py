#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : device_status.py
# @Date : 2021-02-24-10-32
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
device_status.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import sensors
from kalao.utils import database
from kalao.rtc import gpu_control


def read_all():

    rtc_sensors = {}
    sensors.init()

    try:
        for chip in sensors.iter_detected_chips():
            #print '%s at %s' % (chip, chip.adapter_name)
            for feature in chip:
                #print '  %s: %.2f' % (feature.label, feature.get_value())
                chipname = '_'.join(str(chip).split('-')[:-1])
                sensor_name = chipname + '-' + feature.label
                rtc_sensors[sensor_name.replace(' ',
                                                '_')] = feature.get_value()
    finally:
        sensors.cleanup()

    # rtc_sensors.update(gpu_control.status())

    return rtc_sensors


def database_update():
    values = read_all()
    database.store_monitoring(values)
