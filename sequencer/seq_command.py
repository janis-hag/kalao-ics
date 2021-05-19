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
from kalao.utils import database

from configparser import ConfigParser

from pathlib import Path
import os

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')

# Read config file and create a dict for each section where keys is parameter
parser = ConfigParser()
parser.read(config_path)

ExpTime = parser.get('FLI','ExpTime')
TimeSup = parser.get('FLI','TimeSup')

if ExpTime.replace('.', '', 1).isdigit() and TimeSup.isdigit():
    ExpTime = float(ExpTime)
    TimeSup = int(TimeSup)
else:
    print("Error: wrong values format for 'ExpTime' or 'TimeSup' in kalao.config file ")
    ExpTime = 0
    TimeSup = 0

def dark(q = None, dit = ExpTime, nbPic = 1, filepath = None, **kwargs):
    """
    Turn off lamps, close shutter and take 'nbPic' dark picture of 'dit' exposure time.

    If filepath is not None, store the picture to this path.

    q parameter is Queue object for multithreads communication.
    """

    if core.lamps_off() != 0:
        print("Error: failed to turn off lamps")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    # Check if an abort was requested before taking image was send
    if q != None and not q.empty():
        q.get()
        return

    # Take nbPic image
    for _ in range(nbPic):
        rValue = control.take_image(dit = dit, filepath = filepath)
        if rValue != 0:
            print(rValue)
            database.store_obs_log({'sequencer_status': 'error'})
            return

    # Check if an abort was requested and send abort to fli cam
    check_abort(q,dit)

    database.store_obs_log({'sequencer_status': 'waiting'})

def dark_abort():
    """
    Send abort instruction to fli camera.

    Change sequencer status to 'waiting'.
    """
    # two cancel are done to avoid concurrency problems
    rValue = control.cancel()
    if(rValue != 0):
        print(rValue)

    time.sleep(1)

    rValue = control.cancel()
    if(rValue != 0):
        print(rValue)

    database.store_obs_log({'sequencer_status': 'waiting'})

def tungsten_FLAT(q = None, beck = None, dit = ExpTime, filepath = None, **kwargs):
    """
    1. Close shutter
    2. Move flip mirror up
    3. Turn tungsten lamp on
    4. Select filter
    5. Take picture
    6. Turn off tungsten lamp
    """

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    if flip_mirror.up() != 'UP':
        print("Error: flip mirror did not go up")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    tungsten.on(beck = beck)

    #Select Filter

    # Check if an abort was requested
    if q != None not q.empty():
        q.get()
        return

    rValue = control.take_image(dit = dit, filepath = filepath)
    if rValue != 0:
        print(rValue)
        tungsten.off(beck = beck)
        database.store_obs_log({'sequencer_status': 'error'})
        return

    check_abort(q,dit)
    tungsten.off(beck = beck)
    database.store_obs_log({'sequencer_status': 'waiting'})

def sky_FLAT(q = None, dit = ExpTime, filepath = None, **kwargs):
    if core.lamps_off() != 0:
        print("Error: failed to turn off lamps")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    if flip_mirror.down() != 'DOWN':
        print("Error: flip mirror did not go down")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    if shutter.open() != 'OPEN':
        print("Error: failed to open the shutter")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    #Select Fitler

    # Check if an abort was requested
    if q != None not q.empty():
        q.get()
        return

    rValue = control.take_image(dit = dit, filepath = filepath)
    if rValue != 0:
        print(rValue)
        database.store_obs_log({'sequencer_status': 'error'})
        return

    check_abort(q,dit)

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")

    database.store_obs_log({'sequencer_status': 'waiting'})

def target_observation(q = None, dit = ExpTime, filepath = None, **kwargs):
    if core.lamps_off() != 0:
        print("Error: failed to turn off lamps")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    if shutter.open() != 'OPEN':
        print("Error: failed to open the shutter")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    if flip_mirror.down() != 'DOWN':
        print("Error: flip mirror did not go down")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    #Select Filter
    #Centre on target
    #cacao.close_loop()
    #Monitor AO and cancel exposure if needed

    rValue = control.take_image(dit = dit, filepath = filepath)
    if rValue != 0:
        # store to mongo db instead of printing.
        print(rValue)
        database.store_obs_log({'sequencer_status': 'error'})
        return

    check_abort(q,dit)

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")

    database.store_obs_log({'sequencer_status': 'waiting'})


def AO_loop_calibration(q = None, intensity = 0, **kwargs):

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    if flip_mirror.up() != 'UP':
        print("Error: flip mirror did not go up")
        database.store_obs_log({'sequencer_status': 'error'})
        return

    laser.set_intensity(intensity)
    #cacao.start_calib()

    check_abort(q,dit)
    laser.set_intensity(0)
    database.store_obs_log({'sequencer_status': 'waiting'})


def check_abort(q, dit):
    # Check every sec if Queue object q is empty
    # if not, break while sleep
    t = 0
    while t < dit + TimeSup:
        t += 1
        time.sleep(1)
        print(".")
        if q != None and not q.empty():
            q.get()
            break

commandDict = {
    "kal_dark":                 dark,
    "kal_dark_abort":           dark_abort,
    "kal_tungsten_FLAT":        tungsten_FLAT,
    "kal_sky_FLAT":             sky_FLAT,
    "kal_target_observation":   target_observation,
    "kal_AO_loop_calibration":  AO_loop_calibration
}
