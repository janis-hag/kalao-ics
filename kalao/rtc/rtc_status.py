#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : rtc_status.py
# @Date : 2021-02-24-10-32
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
rtc_status.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

from kalao.rtc import gpu_control

import sensors


def read_all_sensors():
    rtc_sensors = {}

    sensors.init()

    try:
        for chip in sensors.iter_detected_chips():
            for feature in chip:
                chipname = '_'.join(str(chip).split('-')[:-1])
                sensor_name = chipname + '-' + feature.label
                rtc_sensors[sensor_name.replace(' ',
                                                '_')] = feature.get_value()
    finally:
        sensors.cleanup()

    # rtc_sensors.update(gpu_control.status())

    return rtc_sensors
