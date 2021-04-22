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
from kalao.plc import core
from kalao.fli import control

from configparser import ConfigParser

from pathlib import Path
import os

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')

# Read config file and create a dict for each section where keys is parameter
parser = ConfigParser()
parser.read(config_path)

ExpTime = parser.getfloat('FLI','ExpTime')
TimeSup = parser.getint('FLI','TimeSup')

def dark(q = None, dit = ExpTime, filepath = None, **kwargs):
    if core.lamps_off() != 0:
        print("Error: failed to turn off lamps")
    else:
        print("Lamps off OK")

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")
    else:
        print("Shutter closed OK")

    # Check if an abort was requested
    if not q.empty():
        q.get()
        dit = -1
        TimeSup = 0

    rValue = control.take_image(dit = dit, filepath = filepath)
    if rValue != 0:
        print(rValue)
    else:
        print("Image taken OK")

    # Check every sec if Queue object q is empty
    # if not, break while sleep
    t = 0
    while t < dit + TimeSup:
        t += 1
        time.sleep(1)
        print(".")
        if not q.empty():
            q.get()
            break

    # STORE "SEQ_SERVER FREE" TO MONGODB

def dark_abort():
    # two cancel are done to avoid concurrency problems
    rValue = control.cancel()
    if(rValue != 0):
        print(rValue)

    time.sleep(1)

    rValue = control.cancel()
    if(rValue != 0):
        print(rValue)

def tungsten_FLAT(beck = None, dit = ExpTime, filepath = None, **kwargs):
    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")

    print(tungsten.on(beck = beck))

    if flip_mirror.up() != 'UP':
        print("Error: flip mirror did not go up")

    #Select Filter

    rValue = control.take_image(dit = dit, filepath = filepath)
    if rValue != 0:
        # store to mongo db instead of printing.
        print(rValue)

    tungsten.off(beck = beck)

def sky_FLAT(dit = ExpTime, filepath = None, **kwargs):
    if core.lamps_off() != 0:
        print("Error: failed to turn off lamps")

    if flip_mirror.down() != 'DOWN':
        print("Error: flip mirror did not go down")

    if shutter.open() != 'OPEN':
        print("Error: failed to open the shutter")

    #Select Fitler

    rValue = control.take_image(dit = dit, filepath = filepath)
    if rValue != 0:
        # store to mongo db instead of printing.
        print(rValue)

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")

def target_observation(dit = ExpTime, filepath = None, **kwargs):
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

    rValue = control.take_image(dit = dit, filepath = filepath)
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
    "kal_dark_abort":           dark_abort,
    "kal_tungsten_FLAT":        tungsten_FLAT,
    "kal_sky_FLAT":             sky_FLAT,
    "kal_target_observation":   target_observation,
    "kal_AO_loop_calibration":  AO_loop_calibration
}
