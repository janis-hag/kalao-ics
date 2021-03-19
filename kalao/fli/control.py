#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : control.py
# @Date : 2021-03-18-10-02
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
control.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from ..utils import kalao_time
import requests
#from datetime import datetime


def take_science_exposure(dit=0.05, filepath=None):
    acquire(dit,filepath)

def acquire(dit=0.05, filepath=None):

    if filepath is None:
        filename = 'KALAO.' + kalao_time.get_isotime() + '.fits'
        filepath = '/home/kalao/data/science/'+filename
    params = {'exptime': dit, 'filepath': filepath}
    req = send_request('acquire', params)
    # store to mongo db instead of printing.
    print(req.status_code)
    print(req.text)

def send_request(type, params):

    url = 'http://127.0.0.1:9080/'+type
    req = requests.post(url, json = params)

    return req
