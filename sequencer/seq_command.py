#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import sys
from os import path
sys.path.append(path.dirname(path.abspath(path.dirname(__file__))))

from kalao.plc import shutter
from kalao.plc import calib_unit
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten
from kalao.fli import control

from configparser import ConfigParser

# Read config file and create a dict for each section where keys is parameter
parser = ConfigParser()
parser.read('../kalao.config')

ExpTime             = parser.getint('FLI','ExpTime')
ScienceDataStorage  = parser.get('FLI', 'ScienceDataStorage')
TimeSup             = parser.getint('FLI','TimeSup')

# store to mongo db instead of printing.

def dark(q = None, dit = ExpTime, filepath = ScienceDataStorage, **kwargs):
    if core.lamps_off() != 0:
        print("Error: failed to turn off lamps")

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")

    rValue = control.acquire(dit = dit, filepath = filepath)
    if rValue != 0:
        print(rValue)

    # Check every sec if Queue object q is empty
    # if not, break sleep while and seq_server should abort the command
    t = 0
    while(t < dit + TimeSup):
        t += 1
        time.sleep(1)
        if(not q.empty()):
            q.get()
            break

def dark_abort():
    pass

def tungsten_FLAT(beck = None, dit = ExpTime, filepath = ScienceDataStorage, **kwargs):
    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")

    tungsten.on(beck = beck)

    if flip_mirror.up() != 'UP':
        print("Error: flip mirror did not go up")

    #Select Filter

    rValue = control.acquire(dit = dit, filepath = filepath)
    if rValue != 0:
        # store to mongo db instead of printing.
        print(rValue)

    tungsten.off(beck = beck)

def sky_FLAT(dit = ExpTime, filepath = ScienceDataStorage, **kwargs):
    if core.lamps_off() != 0:
        print("Error: failed to turn off lamps")

    if flip_mirror.down() != 'DOWN':
        print("Error: flip mirror did not go down")

    if shutter.open() != 'OPEN':
        print("Error: failed to open the shutter")

    #Select Fitler

    rValue = control.acquire(dit = dit, filepath = filepath)
    if rValue != 0:
        # store to mongo db instead of printing.
        print(rValue)

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")

def target_observation(dit = ExpTime, filepath = ScienceDataStorage, **kwargs):
    if core.lamps_off() != 0:
        print("Error: failed to turn off lamps")

    if shutter.open() != 'OPEN':
        print("Error: failed to open the shutter")

    if flip_mirror.down() != 'DOWN':
        print("Error: flip mirror did not go down")

    #Select Filter
    #Centre on target
    #cacao.close_loop()
    #Monitor AO and cancel exposure if needed

    rValue = control.acquire(dit = dit, filepath = filepath)
    if rValue != 0:
        # store to mongo db instead of printing.
        print(rValue)

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")


def AO_loop_calibration(intensity = 0, **kwargs):

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")

    if flip_mirror.up() != 'UP':
        print("Error: flip mirror did not go up")

    laser.set_intensity(intensity)
    #cacao.start_calib()
    laser.set_intensity(0)


commandDict = {
    "kal_dark":                 dark,
    "kal_tungsten_FLAT":        tungsten_FLAT,
    "kal_sky_FLAT":             sky_FLAT,
    "kal_target_observation":   target_observation,
    "kal_AO_loop_calibration":  AO_loop_calibration
}
