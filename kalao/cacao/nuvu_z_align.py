#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : nuvu_z_align.py
# @Date : 2021-03-04-13-59
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
nuvu_z_align.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

from pyMilk.interfacing.isio_shmlib import SHM

#from toolbox import *
from kalao.cacao.toolbox import *

nuvu_stream = SHM("nuvu_stream")

frame = {}
subapertures = {}

left = (34, 45, 56, 67, 78)

right = (42, 53, 64, 75, 86)


def print_ratio():
    frame, subapertures = get_roi_and_subapertures(
            nuvu_stream.get_data(check=True))
    for i in range(5):
        print(np.mean(subapertures[left[i]]) / np.mean(subapertures[right[i]]))
