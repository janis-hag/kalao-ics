#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : wfs_monitoring.py
# @Date : 2022-05-30-16-22
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
wfs_monitoring.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""
import sys

from kalao.cacao import toolbox
from kalao.plc import laser, flip_mirror
from kalao.utils import file_handling
import schedule
from time import sleep

#turn on laser
#get image from nuvu shm
#save fits with header


def save_wfs_image():

    #turn on laser

    laser.set_intensity(5)
    flip_mirror.up()

    file_path = file_handling.create_night_filepath(
            tmp_night_folder='/home/kalao/data/tmp/wfs')

    cp = toolbox.save_stream_to_fits('nuvu_stream', file_path)

    print("=========================== STDOUT")
    print(cp.stdout)
    print("=========================== STDERR")
    print(cp.stderr)

    file_handling.update_header(file_path)

    return 0


if __name__ == '__main__':

    schedule.every(2).seconds.do(save_wfs_image)

    while True:
        schedule.run_pending()
        sleep(1)
