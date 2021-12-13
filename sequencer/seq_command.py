#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path
import time
from configparser import ConfigParser

# add the necessary path to find the folder kalao for import
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from kalao.plc import core, tungsten, laser, flip_mirror, shutter, filterwheel
from kalao.fli import control
from kalao.utils import file_handling, database
from kalao.cacao import aomanager
import starfinder

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')

# Read config file and create a dict for each section where keys is parameter
parser = ConfigParser()
parser.read(config_path)

Science_storage = parser.get('FLI','ScienceDataStorage')
ExpTime = parser.getfloat('FLI','ExpTime')
TimeSup = parser.getint('FLI','TimeSup')
TungstenStabilisationTime = parser.getint('PLC','TungstenStabilisationTime')
TungstenWaitSleep = parser.getint('PLC','TungstenWaitSleep')
DefaultFlatList = parser.get('Calib','DefaultFlatList').replace(' ','').replace('\n','').split(',')

def dark(**seq_args):
    """
    1. Turn off lamps
    2. Close shutter
    3. Take 'nbPic' dark picture of 'dit' exposure time.

    If an error occurs, stores the status of the sequencer in 'ERROR', otherwise stores it in 'WAITING'

    :param q: Queue object for multithreads communication
    :param dit: float for exposition time
    :param nbPic: number of picture taken
    :param filepath: If filepath is not None, store the picture to this path
    :param kwargs: supports additional arguments
    :return: nothing
    """

    q=seq_args.get('q')
    dit=seq_args.get('dit')
    nbPic=seq_args.get('nbPic')

    if None in (q, dit, nbPic):
        database.store_obs_log({'sequencer_log': 'Missing keyword in dark function call'})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if core.lamps_off() != 0:
        database.store_obs_log({'sequencer_log':"Error: failed to turn off lamps"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if shutter.shutter_close() != 'CLOSE':
        database.store_obs_log({'sequencer_log':"Error: failed to close the shutter"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    # Check if an abort was requested before taking image was send
    if q != None and not q.empty():
        q.get()
        return -1


    filepath = file_handling.create_night_filepath()

    # Take nbPic image
    for _ in range(nbPic):
        rValue = control.take_image(dit = dit, filepath = filepath)

        image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values']
        file_handling.save_tmp_picture(image_path)

        if rValue != 0:
            database.store_obs_log({'sequencer_log':rValue})
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        # block for each picture and check if an abort was requested
        if check_abort(q, dit) == -1:
            return -1

    database.store_obs_log({'sequencer_status': 'WAITING'})


def dark_abort():
    """
    Send abort instruction to fli camera and change sequencer status to 'WAITING'.
    :return: nothing
    """
    # two cancel are done to avoid concurrency problems
    rValue = control.cancel()
    if(rValue != 0):
        # TODO handle error
        database.store_obs_log({'sequencer_log':rValue})

    time.sleep(1)

    rValue = control.cancel()
    if(rValue != 0):
        # TODO handle error
        database.store_obs_log({'sequencer_log':rValue})

    database.store_obs_log({'sequencer_status': 'WAITING'})


def tungsten_FLAT(**seq_args):
    """
    1. Close shutter
    2. Move flip mirror up
    3. Turn tungsten lamp on
    4. Select filter
    5. Take picture
    6. Turn off tungsten lamp

    If an error occurs, stores the status of the sequencer in 'ERROR', otherwise stores it in 'WAITING'

    :param q: Queue object for multithreads communication
    :param beck:
    :param dit: float for exposition time
    :param filepath: If filepath is not None, store the picture to this path
    :param kwargs: supports additional arguments
    :return: nothing
    """

    rValue = tungsten.on()
    if(rValue != 0):
        database.store_obs_log({'sequencer_log': 'Could not turn on tungsten lamp: '+tungsten.status()['sErrorText']})
        return -1

    q = seq_args.get('q')
    filter_list = seq_args.get('filter_list')
    filepath = seq_args.get('filepath')

    if None in (q):
        database.store_obs_log({'sequencer_log': 'Missing keyword in target_observation function call'})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if filter_list is None:
        filter_list = DefaultFlatList

    if tungsten.on() != 2:
        database.store_obs_log({'sequencer_log': "Error: failed to turn on tungsten lamp"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if shutter.shutter_close() != 'CLOSE':
        database.store_obs_log({'sequencer_log': "Error: failed to close the shutter"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if flip_mirror.up() != 'UP':
        database.store_obs_log({'sequencer_log': 'Error: flip mirror did not go up'})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if filterwheel.set_position(filter_list[0]) == -1:
        database.store_obs_log({'sequencer_log': 'Error: problem with filter selection'})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    # Check if an abort was requested
    if q != None and not q.empty():
        q.get()
        return

    if filepath is None:
        filepath = file_handling.create_night_filepath()
    else:
        # TODO, verify that temporary_path is in the filepath
        temporary_path = file_handling.create_night_folder()

    while(tungsten.get_switch_time() < TungstenStabilisationTime):
        # Wait for tungsten to warm up
        # Check if an abort was requested
        # block for each picture and check if an abort was requested
        if check_abort(q,1) == -1:
            return -1

        # Check if lamp is still on
        if tungsten.status()['nStatus'] != 2:
            database.store_obs_log({'sequencer_log': 'Tungsten lamp unexpectedly turned off.'})
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        time.sleep(TungstenWaitSleep)

    for filter_name in filter_list:

        if filterwheel.set_position(filter_name) == -1:
            database.store_obs_log({'sequencer_log': 'Error: problem with filter selection'})
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        # Take nbPic image
        dit = tungsten.get_flat_dits()[filter_name]

        image_path = file_handling.create_night_filepath()

        rValue = control.take_image(dit=dit, filepath=image_path)

        #image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values']
        file_handling.save_tmp_picture(image_path)

        if rValue != 0:
            database.store_obs_log({'sequencer_log':rValue})
            #tungsten.off()
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        # block for each picture and check if an abort was requested
        if check_abort(q, dit) == -1:
            #tungsten.off()
            return -1

    # TODO move tungsen.off() to start of other commands so that the lamp stays on if needed
    #tungsten.off()
    database.store_obs_log({'sequencer_status': 'WAITING'})


def tungsten_FLAT_abort():
    """
    Send abort instruction to fli camera and change sequencer status to 'WAITING'.
    :return: nothing
    """
    # two cancel are done to avoid concurrency problems
    rValue = control.cancel()
    if(rValue != 0):
        # TODO handle error
        database.store_obs_log({'sequencer_log':rValue})

    time.sleep(1)

    rValue = control.cancel()
    if(rValue != 0):
        # TODO handle error
        database.store_obs_log({'sequencer_log':rValue})

    database.store_obs_log({'sequencer_status': 'WAITING'})


def sky_FLAT(**seq_args):
    """
    1. Turn off lamps
    2. Move flip mirror down
    3. Open shutter
    4. Select filter
    5. Take picture
    6. Close shutter

    :param q: Queue object for multithreads communication
    :param dit: float for exposition time
    :param filepath: If filepath is not None, store the picture to this path
    :param kwargs: supports additional arguments
    :return: nothing
    """

    q = seq_args.get('q')
    filter_list = seq_args.get('filter_list')
    filepath = seq_args.get('filepath')
    dit = seq_args.get('dit')

    if None in (q, dit, filepath):
        # TODO verify which arguments are actually needed.
        database.store_obs_log({'sequencer_log': 'Missing keyword in dark function call'})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if filter_list is None:
        filter_list = DefaultFlatList

    if core.lamps_off() != 0:
        database.store_obs_log({'sequencer_log':"Error: failed to turn off lamps"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if flip_mirror.down() != 'DOWN':
        database.store_obs_log({'sequencer_log':"Error: flip mirror did not go down"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if shutter.shutter_open() != 'OPEN':
        database.store_obs_log({'sequencer_log':"Error: failed to open the shutter"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if filterwheel.set_position(filter_list[0]) == -1:
        database.store_obs_log({'sequencer_log':"Error: problem with filter selection"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return
    # Check if an abort was requested
    if q != None and not q.empty():
        q.get()
        return

    for filter_name in filter_list:

        if filterwheel.set_position(filter_name) == -1:
            database.store_obs_log({'sequencer_log': 'Error: problem with filter selection'})
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        # Take nbPic image
        dit = tungsten.get_flat_dits()[filter_name]

        image_path = file_handling.create_night_filepath()

        rValue = control.take_image(dit=dit, filepath=image_path)

        #image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values']
        file_handling.save_tmp_picture(image_path)

        if rValue != 0:
            database.store_obs_log({'sequencer_log':rValue})
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        # block for each picture and check if an abort was requested
        if check_abort(q, dit) == -1:
            return -1


    if shutter.shutter_close() != 'CLOSE':
        database.store_obs_log({'sequencer_log':"Error: failed to close the shutter"})

    database.store_obs_log({'sequencer_status': 'WAITING'})


def target_observation(**seq_args): #q = None, dit = ExpTime, filepath = None, filter_arg = None, **kwargs):
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

    :param q: Queue object for multithreads communication
    :param dit: float for exposition time
    :param filepath: If filepath is not None, store the picture to this path
    :param kwargs: supports additional arguments
    :return: nothing
    """

    q = seq_args.get('q')
    filter_arg = seq_args.get('filter_arg')
    filepath = seq_args.get('filepath')
    dit = seq_args.get('dit')

    if None in (q, dit):
        database.store_obs_log({'sequencer_log': 'Missing keyword in target_observation function call'})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if core.lamps_off() != 0:
        database.store_obs_log({'sequencer_log':"Error: failed to turn off lamps"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if flip_mirror.down() != 'DOWN':
        database.store_obs_log({'sequencer_log':"Error: flip mirror did not go down"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if shutter.shutter_open() != 'OPEN':
        database.store_obs_log({'sequencer_log':"Error: failed to open the shutter"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if starfinder.centre_on_target() == -1:
        database.store_obs_log({'sequencer_log':"Error: problem with centre on target"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if filter_arg is None:
        database.store_obs_log({'sequencer_log':"Warning: no filter specified for take image, using clear"})
        filter_arg = 'clear'

    if filterwheel.set_position(filter_arg) == -1:
        database.store_obs_log({'sequencer_log':"Error: problem with filter selection"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    aomanager.close_loop()

    temporary_path = file_handling.create_night_folder()

    rValue = control.take_image(dit = dit, filepath = filepath)

    #Monitor AO and cancel exposure if needed

    image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values']
    file_handling.save_tmp_picture(image_path)

    if rValue != 0:
        database.store_obs_log({'sequencer_log':rValue})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if check_abort(q, dit) == -1:
        return -1

    database.store_obs_log({'sequencer_status': 'WAITING'})


def target_observation_abort():
    """
    Send abort instruction to fli camera and change sequencer status to 'WAITING'.
    :return: nothing
    """
    # two cancel are done to avoid concurrency problems
    rValue = control.cancel()
    if(rValue != 0):
        database.store_obs_log({'sequencer_log':rValue})

    time.sleep(1)

    rValue = control.cancel()
    if(rValue != 0):
        database.store_obs_log({'sequencer_log':rValue})

    database.store_obs_log({'sequencer_status': 'WAITING'})


def AO_loop_calibration(q = None, intensity = 0, **kwargs):
    """
    1. Close shutter
    2. Move flip mirror up
    3. Set laser intensity to 'intensity' parameter
    4. Start cacao calibration
    5. Set laser intensity to 0

    :param q: Queue object for multithreads communication
    :param intensity: float
    :param kwargs: supports additional arguments
    :return: nothing
    """

    if shutter.shutter_close() != 'CLOSE':
        database.store_obs_log({'sequencer_log':"Error: failed to close the shutter"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if flip_mirror.up() != 'UP':
        database.store_obs_log({'sequencer_log':"Error: flip mirror did not go up"})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    laser.set_intensity(intensity)

    # TODO core AO part missing
    #cacao.start_calib()

    laser.disable()

    database.store_obs_log({'sequencer_status': 'WAITING'})


def lamp_on():
    """
    Turn tungsten lamp on
    :return: nothing
    """

    rValue = tungsten.on()
    if(rValue != 0):
        # TODO handle error
        database.store_obs_log({'sequencer_log':rValue})

    database.store_obs_log({'sequencer_status': 'WAITING'})


def end():
    """
    End of instrument operation, go into standby mode
    :return: nothing
    """
    # two cancel are done to avoid concurrency problems

    rValue = tungsten.off()
    if (rValue != 0):
        # TODO handle error
        database.store_obs_log({'sequencer_log': rValue})

    rValue = laser.disable()
    if (rValue != 0):
        # TODO handle error
        database.store_obs_log({'sequencer_log': rValue})

    rValue = shutter.shutter_close()
    if (rValue != 0):
        # TODO handle error
        database.store_obs_log({'sequencer_log': rValue})

    database.store_obs_log({'sequencer_log': 'END received moving into standby.'})

    database.store_obs_log({'sequencer_status': 'WAITING'})



def check_abort(q, dit, AO = False):
    """
    Blocking function for exposition time
    Check every sec if Queue object q is empty
    if not, then an abort is required. Break the while sleep

    :param q:
    :param dit:
    :return: nothing
    """

    t = 0
    while t < dit + TimeSup:
        t += 1
        time.sleep(1)
        print(".")
        # Check if an abort is required
        if q != None and not q.empty():
            q.get()
            # TODO add update_plc_monitoring
            return -1
        if AO and aomanager.check_loop() == -1:
            return -1
    return 0


commandDict = {
    "kal_dark":                     dark,
    "kal_dark_abort":               dark_abort,
    "kal_tungsten_FLAT":            tungsten_FLAT,
    "kal_tungsten_FLAT_abort":      tungsten_FLAT_abort,
    "kal_sky_FLAT":                 sky_FLAT,
    "kal_target_observation":       target_observation,
    "kal_target_observation_abort": target_observation_abort,
    "kal_AO_loop_calibration":      AO_loop_calibration
}
