#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : inject_turbulences.py
# @Date : 2022-03-01-10-58
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
inject_turbulences.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import argparse
import subprocess
from subprocess import PIPE, STDOUT

import config


def run(args):
    input = f"""
    loadfits "{args.file}" turbulences_cube
    readshmim {args.stream}
    streamburst turbulences_cube {args.stream} {args.rate}
    exitCLI
    """

    cp = subprocess.run(['milk'], input=input, encoding='utf8', stdout=PIPE,
                        stderr=STDOUT)

    print('=========================== STDOUT')

    print(cp.stdout)

    print('=========================== STDERR')

    print(cp.stderr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Inject turbulences on DM.')
    parser.add_argument('-f', action="store", dest="file", required=True,
                        type=str, help='File containing the turbulences cube')
    parser.add_argument('-r', action="store", dest="rate", required=True,
                        type=int, help='Framerate of the turbulences')
    parser.add_argument(
        '-s', action="store", dest="stream", default=config.SHM.DM_TURBULENCES,
        type=str, help='Stream in which the turbulences will be injected')

    args = parser.parse_args()

    run(args)
