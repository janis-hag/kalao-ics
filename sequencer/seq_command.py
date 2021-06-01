#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
import time
from configparser import ConfigParser

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from kalao.plc import shutter
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten
from kalao.plc import core
from kalao.fli import control
from kalao.utils import database


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
    1. Turn off lamps
    2. Close shutter
    3. Take 'nbPic' dark picture of 'dit' exposure time.

    If an error occurs, stores the status of the sequencer in 'ERROR', otherwise stores it in 'WAITING'

    @param q: Queue object for multithreads communication
    @param dit: float for exposition time
    @param nbPic: number of picture taken
    @param filepath: If filepath is not None, store the picture to this path
    @param kwargs: supports additional arguments
    @return: nothing
    """

    if core.lamps_off() != 0:
        print("Error: failed to turn off lamps")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
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
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return
        # Check if an abort was requested and send abort to fli cam
        check_abort(q, dit)

    database.store_obs_log({'sequencer_status': 'waiting'})

def dark_abort():
    """
    Send abort instruction to fli camera and change sequencer status to 'waiting'.
    @return: nothing
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

    If an error occurs, stores the status of the sequencer in 'ERROR', otherwise stores it in 'WAITING'

    @param q: Queue object for multithreads communication
    @param beck:
    @param dit: float for exposition time
    @param filepath: If filepath is not None, store the picture to this path
    @param kwargs: supports additional arguments
    @return: nothing
    """

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if flip_mirror.up() != 'UP':
        print("Error: flip mirror did not go up")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    tungsten.on(beck = beck)

    #Select Filter

    # Check if an abort was requested
    if q != None and not q.empty():
        q.get()
        return

    rValue = control.take_image(dit = dit, filepath = filepath)
    if rValue != 0:
        print(rValue)
        tungsten.off(beck = beck)
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    check_abort(q,dit)
    tungsten.off(beck = beck)
    database.store_obs_log({'sequencer_status': 'waiting'})

def sky_FLAT(q = None, dit = ExpTime, filepath = None, **kwargs):
    """
    1. Turn off lamps
    2. Move flip mirror down
    3. Open shutter
    4. Select filter
    5. Take picture
    6. Close shutter

    @param q: Queue object for multithreads communication
    @param dit: float for exposition time
    @param filepath: If filepath is not None, store the picture to this path
    @param kwargs: supports additional arguments
    @return: nothing
    """
    if core.lamps_off() != 0:
        print("Error: failed to turn off lamps")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if flip_mirror.down() != 'DOWN':
        print("Error: flip mirror did not go down")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if shutter.open() != 'OPEN':
        print("Error: failed to open the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    #Select Fitler

    # Check if an abort was requested
    if q != None and not q.empty():
        q.get()
        return

    rValue = control.take_image(dit = dit, filepath = filepath)
    if rValue != 0:
        print(rValue)
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    check_abort(q,dit)

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")

    database.store_obs_log({'sequencer_status': 'waiting'})

def target_observation(q = None, dit = ExpTime, filepath = None, **kwargs):
    """
    1. Turn off lamps
    2. Move flip mirror down
    3. Open shutter
    4. Select filter
    5. Center on target
    6. Close cacao loop ?
    7. Monitor AO and cancel exposure if needed
    8. Take picture
    9. Close shutter

    @param q: Queue object for multithreads communication
    @param dit: float for exposition time
    @param filepath: If filepath is not None, store the picture to this path
    @param kwargs: supports additional arguments
    @return: nothing
    """
    if core.lamps_off() != 0:
        print("Error: failed to turn off lamps")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if flip_mirror.down() != 'DOWN':
        print("Error: flip mirror did not go down")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if shutter.open() != 'OPEN':
        print("Error: failed to open the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    #Select Filter
    #Centre on target
    #cacao.close_loop()
    #Monitor AO and cancel exposure if needed

    rValue = control.take_image(dit = dit, filepath = filepath)
    if rValue != 0:
        # store to mongo db instead of printing.
        print(rValue)
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    check_abort(q,dit)

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")

    database.store_obs_log({'sequencer_status': 'waiting'})


def AO_loop_calibration(q = None, intensity = 0, **kwargs):
    """
    1. Close shutter
    2. Move flip mirror up
    3. Set laser intensity to 'intensity' parameter
    4. Start cacao calibration
    5. Set laser intensity to 0

    @param q: Queue object for multithreads communication
    @param intensity: float
    @param kwargs: supports additional arguments
    @return: nothing
    """

    if shutter.close() != 'CLOSE':
        print("Error: failed to close the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if flip_mirror.up() != 'UP':
        print("Error: flip mirror did not go up")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    laser.set_intensity(intensity)
    #cacao.start_calib()
    laser.set_intensity(0)
    database.store_obs_log({'sequencer_status': 'waiting'})


def check_abort(q, dit):
    """
    Blocking function for exposition time
    Check every sec if Queue object q is empty
    if not, then an abort is required. Break the while sleep

    @param q:
    @param dit:
    @return: nothing
    """

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
