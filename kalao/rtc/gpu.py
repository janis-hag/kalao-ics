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

import pandas as pd


def status():
    '''
    Reads the status of the nvidia GPU using the nvidia-smi command with csv output and returns it as a dictionary

    :return: status_dict a dictionary contining all the gpu status values
    '''

    out_str = subprocess.run([
        'nvidia-smi',
        '--query-gpu=memory.total,memory.used,memory.free,temperature.gpu,power.draw,utilization.gpu,utilization.memory',
        '--format=csv,nounits'
    ], capture_output=True).stdout.decode('utf8')

    status_frame = pd.read_csv(io.StringIO(out_str))
    status_frame.columns = [
        c.split(' ')[0] for c in list(status_frame.columns.str.strip())
    ]

    status_frame = status_frame.to_dict('records')[0]

    status_dict = {}

    status_dict['gpu_current_temp'] = status_frame['temperature.gpu']
    status_dict['gpu_power_draw'] = status_frame['power.draw']
    status_dict['gpu_used_memory'] = status_frame['memory.used']
    status_dict['gpu_free_memory'] = status_frame['memory.free']
    status_dict['gpu_load'] = status_frame['utilization.gpu']

    return status_dict
