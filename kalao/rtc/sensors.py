#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : sensors.py
# @Date : 2021-02-24-10-32
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
sensors.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""
from typing import Any

import sensors


def status() -> dict[str, Any]:
    rtc_sensors = {}

    sensors.init()

    try:
        for chip in sensors.iter_detected_chips():
            for feature in chip:
                chipname = '_'.join(str(chip).split('-')[:-1])
                sensor_name = chipname + '-' + feature.label
                rtc_sensors[
                    'rtc_' +
                    sensor_name.replace(' ', '_')] = feature.get_value()
    finally:
        sensors.cleanup()

    return rtc_sensors
