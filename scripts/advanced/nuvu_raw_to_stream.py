#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : nuvu_raw_to_stream
# @Date : 2022-02-11-10-21
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
nuvu_raw_to_stream.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import numpy as np

from pyMilk.interfacing.isio_shmlib import SHM


def run():
    # initialise stream
    cam = SHM('nuvu_raw')

    # Get initial data
    data = cam.get_data(check=True)[4:-2, ::8].astype(np.int16)

    # Create stream
    nuvu_out_stream = SHM(
            'nuvu_proc_stream',
            data,  # 30x30 int16 np.array
            location=-1,  # CPU
            shared=True,  # Shared
    )

    while True:
        data = cam.get_data(check=True)[4:-2, ::8].astype(np.int16)
        # Get new data and refresh stream
        nuvu_out_stream.set_data(data)


if __name__ == '__main__':
    run()
