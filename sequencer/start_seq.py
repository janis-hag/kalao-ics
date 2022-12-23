#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : system.py
# @Date : 2021-08-16-13-33
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
star_seq.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

from sequencer import seq_init
from sequencer import seq_server
from sequencer import system
from kalao.utils import database, kalao_time

if __name__ == '__main__':

    system.print_and_log("Server starting: " + str(kalao_time.now()))

    database.store_obs_log({'sequencer_status': 'INITIALISING'})

    if seq_init.initialisation() == 0:
        print("Initialisation OK.")
    else:
        print("Error: Initialisation failed")

    seq_server.seq_server()
