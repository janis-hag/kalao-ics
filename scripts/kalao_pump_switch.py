#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : kalao_pump_switch.sh
# @Date : 2023-01-12-14-12
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
kalao_pump_switch.py is part of the KalAO Instrument Control Software it is a maintenance script used to switch
the water cooling pump from on to off and opposite.
(KalAO-ICS).
"""

from kalao.plc import temperature_control
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--on', help='Turn pump ON', action='store_true')
    parser.add_argument('--off', dest='on', action='store_false')
    parser.set_defaults(feature=False)
    args = parser.parse_args()

    #if temperature_control.pump_status() == 'ON':
    if args.on:
        print("Switching pump ON")
        temperature_control.pump_on()
    else:
        print("Switching pump OFF")
        temperature_control.pump_off()
