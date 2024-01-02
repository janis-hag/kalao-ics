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

from kalao.cacao import toolbox

import config


def run():
    nuvu_in_stream = toolbox.open_stream_once(config.Streams.NUVU_RAW, {})
    nuvu_out_stream = toolbox.open_or_create_stream(config.Streams.NUVU,
                                                    (64, 64), np.int16)

    while True:
        data = nuvu_in_stream.get_data(check=True)[4:-2, ::8].astype(np.int16)
        nuvu_out_stream.set_data(data)


if __name__ == '__main__':
    run()
