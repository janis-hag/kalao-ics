#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : sensors.py
# @Date : 2021-02-24-10-32
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
gpu_control.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""
import subprocess
import pprint

def full_status():
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


def status():

    status_dict = {}
    full_dict = full_status()

    status_dict['gpu_current_temp'] = full_dict['GPU Current Temp'].split(' ')[0]
    status_dict['gpu_power_draw'] = full_dict['Power Draw'].split(' ')[0]
    status_dict['gpu_used_memory'] = full_dict['Used'].split(' ')[0]
    status_dict['gpu_free_memory'] = full_dict['Free'].split(' ')[0]
    status_dict['gpu_load'] = full_dict['Gpu'].split(' ')[0]


    return status_dict