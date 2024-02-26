#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : sensors.py
# @Date : 2021-02-24-10-32
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
gpu.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""
import io
import subprocess
from typing import Any

import pandas as pd


def status() -> dict[str, Any]:
    '''
    Reads the status of the nvidia GPU using the nvidia-smi command with csv output and returns it as a dictionary

    :return: status_dict a dictionary contining all the gpu status values
    '''

    out_str = subprocess.run([
        'nvidia-smi',
        '--query-gpu=memory.total,memory.used,memory.free,temperature.gpu,power.draw,utilization.gpu,utilization.memory',
        '--format=csv,nounits'
    ], capture_output=True).stdout.decode()

    status_frame = pd.read_csv(io.StringIO(out_str))

    status_dict = {}

    status_dict['gpu_current_temp'] = status_frame['temperature.gpu'][0]
    status_dict['gpu_power_draw'] = status_frame['power.draw [W]'][0]
    status_dict['gpu_used_memory'] = status_frame['memory.used [MiB]'][0]
    status_dict['gpu_free_memory'] = status_frame['memory.free [MiB]'][0]
    status_dict['gpu_load'] = status_frame['utilization.gpu [%]'][0]

    return status_dict
