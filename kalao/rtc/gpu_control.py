#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : temperatures.py
# @Date : 2021-02-24-10-32
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
gpu_control.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""
import subprocess
import pprint

def status():
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

def get_temp():
    '''
    Reads the gpu status and extracts the current temperature values stripped of the C unit

    :return: current gpu temperature
    '''
    return status()['GPU Current Temp'].split(' ')[0]