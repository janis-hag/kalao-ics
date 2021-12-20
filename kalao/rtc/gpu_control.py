#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : device_status.py
# @Date : 2021-02-24-10-32
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
gpu_control.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""
import subprocess
import io
import pandas as pd


def tatus():
    '''
    Reads the status of the nvidia GPU using the nvidia-smi command with csv output and returns it as a dictionary

    :return: status_dict a dictionary contining all the gpu status values
    '''

    out_str = subprocess.run(['nvidia-smi', '--query-gpu=memory.total,memory.used,memory.free,temperature.gpu,power.draw,utilization.gpu,utilization.memory','--format=csv,nounits'], capture_output=True).stdout.decode('utf8')

    status_frame = pd.read_csv(io.StringIO(out_str))
    #status_frame.columns = status_frame.columns.str.strip()
    status_frame.columns = [c.split(' ')[0] for c in list(status_frame.columns.str.strip())]

    status_frame = status_frame.to_dict('records')[0]

    status_dict = {}

    status_dict['gpu_current_temp'] = status_frame['temperature.gpu']
    status_dict['gpu_power_draw'] = status_frame['power.draw']
    status_dict['gpu_used_memory'] = status_frame['memory.used']
    status_dict['gpu_free_memory'] = status_frame['memory.free']
    status_dict['gpu_load'] = status_frame['utilization.gpu']

    return status_dict


def full_status_parse():
    '''
    Reads the status of the nvidia GPU using the nvidia-smi command and returns it as a dictionary

    :return: status_dict a dictionary contining all the gpu status values
    '''

    out_str = subprocess.run(['nvidia-smi', '-q'], capture_output=True).stdout.decode('utf8')

    out_list = out_str.split('\n')
    status_dict = {}

    for item in out_list:
        try:
            key, val = item.split(':')
            key, val = key.strip(), val.strip()
            status_dict[key] = val
        except:
            pass

    return status_dict


def status_parse():

    status_dict = {}
    full_dict = full_status_parse()

    status_dict['gpu_current_temp'] = full_dict['GPU Current Temp'].split(' ')[0]
    status_dict['gpu_power_draw'] = full_dict['Power Draw'].split(' ')[0]
    status_dict['gpu_used_memory'] = full_dict['Used'].split(' ')[0]
    status_dict['gpu_free_memory'] = full_dict['Free'].split(' ')[0]
    status_dict['gpu_load'] = full_dict['Gpu'].split(' ')[0]


    return status_dict


'''
"memory.total"
Total installed GPU memory.

"memory.used"
Total memory allocated by active contexts.

"memory.free"
Total free memory.


"temperature.gpu"
 Core GPU temperature. in degrees C.

"temperature.memory"
 HBM memory temperature. in degrees C.
 
"power.draw"
The last measured power draw for the entire board, in watts. Only available if power management is supported. This reading is accurate to within +/- 5 watts.

"utilization.gpu"
Percent of time over the past sample period during which one or more kernels was executing on the GPU.
The sample period may be between 1 second and 1/6 second depending on the product.

"utilization.memory"
Percent of time over the past sample period during which global (device) memory was being read or written.
The sample period may be between 1 second and 1/6 second depending on the product.


'''