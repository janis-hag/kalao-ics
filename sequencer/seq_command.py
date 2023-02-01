#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : status.py
# @Date : 2021-01-02-16-50
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
seq_command.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import sys
import os
from pathlib import Path
import time
from configparser import ConfigParser
import datetime

# add the necessary path to find the folder kalao for import
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from kalao.plc import core, tungsten, laser, flip_mirror, shutter, filterwheel
from kalao.fli import camera
from kalao.utils import file_handling, database, database_updater, kalao_time
from kalao.cacao import aomanager
from sequencer import starfinder, system
# from tcs_communication import t120

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[1], 'kalao.config')

# Read config file and create a dict for each section where keys is parameter
parser = ConfigParser()
parser.read(config_path)

Science_storage = parser.get('FLI', 'ScienceDataStorage')
ExpTime = parser.getfloat('FLI', 'ExpTime')
SetupTime = parser.getint('FLI', 'SetupTime')
TungstenStabilisationTime = parser.getint('PLC', 'TungstenStabilisationTime')
TungstenWaitSleep = parser.getint('PLC', 'TungstenWaitSleep')
DefaultFlatList = parser.get('Calib',
                             'DefaultFlatList').replace(' ', '').replace(
                                     '\n', '').split(',')
PointingWaitTime = parser.getfloat('SEQ', 'PointingWaitTime')
PointingTimeOut = parser.getfloat('SEQ', 'PointingTimeOut')


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

    q = seq_args.get('q')
    dit = seq_args.get('dit')
    nbPic = seq_args.get('nbPic')

    if nbPic is None:
        nbPic = 1

    if None in (q, dit, nbPic):
        system.print_and_log('Missing keyword in dark function call')
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if core.lamps_off() != 0:
        system.print_and_log("Error: failed to turn off lamps")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if shutter.shutter_close() != 'CLOSED':
        system.print_and_log("Error: failed to close the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    # Check if an abort was requested before taking image was send
    if q != None and not q.empty():
        q.get()
        return -1

    filepath = file_handling.create_night_filepath()

    # Take nbPic image
    for _ in range(nbPic):
        #seq_command_received = database.get_latest_record('obs_log', key='sequencer_command_received')[
        #    'sequencer_command_received']
        rValue, image_path = camera.take_image(dit=dit, filepath=filepath,
                                               sequencer_arguments=seq_args)

        #image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values'][0]
        #file_handling.save_tmp_image(image_path)

        if rValue != 0:
            system.print_and_log('Error' + str(rValue))
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        # block for each picture and check if an abort was requested
        if check_abort(q, dit) == -1:
            database.store_obs_log({'sequencer_status': 'WAITING'})
            return -1

    database.store_obs_log({'sequencer_status': 'WAITING'})


def dark_abort():
    """
    Send abort instruction to fli camera and change sequencer status to 'WAITING'.
    :return: nothing
    """
    # two cancel are done to avoid concurrency problems
    rValue = camera.cancel()
    if (rValue != 0):
        # TODO handle error
        system.print_and_log('Error' + str(rValue))

    time.sleep(1)

    rValue = camera.cancel()
    if (rValue != 0):
        # TODO handle error
        system.print_and_log('Error' + str(rValue))

    database.store_obs_log({'sequencer_status': 'WAITING'})


def tungsten_FLAT(**seq_args):
    """
    1. Close shutter
    2. Move flip mirror up
    3. Turn tungsten lamp on
    4. Select filter
    5. Take picture

    If an error occurs, stores the status of the sequencer in 'ERROR', otherwise stores it in 'WAITING'

    :param q: Queue object for multithreads communication
    :param beck:
    :param dit: float for exposition time
    :param filepath: If filepath is not None, store the picture to this path
    :param kwargs: supports additional arguments
    :return: nothing
    """

    rValue = tungsten.on()
    if (rValue != 'ON'):
        system.print_and_log('Could not turn on tungsten lamp: ' +
                             tungsten.status()['sErrorText'])
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    q = seq_args.get('q')
    filter_list = seq_args.get('filter_list')
    filepath = seq_args.get('filepath')

    # Commented out as it is not clear what is meant to be checked
    # if None in (q):
    #     system.print_and_log('Missing keyword in target_observation function call')
    #     database.store_obs_log({'sequencer_status': 'ERROR'})
    #     return -1

    if filter_list is None:
        filter_list = DefaultFlatList

    if shutter.shutter_close() != 'CLOSED':
        system.print_and_log("Error: failed to close the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if flip_mirror.up() != 'UP':
        system.print_and_log('Error: flip mirror did not go up')
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if filterwheel.set_position(filter_list[0]) == -1:
        system.print_and_log('Error: problem with filter selection')
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    # Check if an abort was requested
    if q != None and not q.empty():
        q.get()
        return

    # if filepath is None:
    #     filepath = file_handling.create_night_filepath()
    # else:
    #     # TODO, verify that temporary_path is in the filepath
    #     temporary_path = file_handling.create_night_folder()

    while (tungsten.get_switch_time() < TungstenStabilisationTime):
        # Wait for tungsten to warm up
        # Check if an abort was requested
        # block for each picture and check if an abort was requested
        database.store_obs_log({'sequencer_status': 'WAITLAMP'})
        if check_abort(q, 1) == -1:
            return -1

        # Check if lamp is still on
        if tungsten.status()['nStatus'] != 2:
            system.print_and_log('Tungsten lamp unexpectedly turned off.')
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        time.sleep(TungstenWaitSleep)
    else:
        database.store_obs_log({'sequencer_status': 'BUSY'})

    for filter_name in filter_list:

        if filterwheel.set_position(filter_name) == -1:
            system.print_and_log('Error: problem with filter selection.')
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        # Take nbPic image
        dit = tungsten.get_flat_dits()[filter_name]

        image_path = file_handling.create_night_filepath()

        rValue, image_path = camera.take_image(dit=dit, filepath=image_path)

        #image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values']
        #file_handling.save_tmp_image(image_path)

        if rValue != 0:
            system.print_and_log(rValue)
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
    rValue = camera.cancel()
    if (rValue != 0):
        # TODO handle error
        system.print_and_log(rValue)

    time.sleep(1)

    rValue = camera.cancel()
    if (rValue != 0):
        # TODO handle error
        system.print_and_log(rValue)

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
        system.print_and_log('Missing keyword in flat function call')
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if filter_list is None:
        filter_list = DefaultFlatList

    if core.lamps_off() != 0:
        system.print_and_log("Error: failed to turn off lamps")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if flip_mirror.down() != 'DOWN':
        system.print_and_log("Error: flip mirror did not go down")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if shutter.shutter_open() != 'OPEN':
        system.print_and_log("Error: failed to open the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if filterwheel.set_position(filter_list[0]) == -1:
        system.print_and_log("Error: problem with filter selection")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return
    # Check if an abort was requested
    if q != None and not q.empty():
        q.get()
        return

    for filter_name in filter_list:

        if filterwheel.set_position(filter_name) == -1:
            system.print_and_log('Error: problem with filter selection')
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        # Take nbPic image
        dit = tungsten.get_flat_dits()[filter_name]

        image_path = file_handling.create_night_filepath()

        rValue, image_path = camera.take_image(dit=dit, filepath=image_path)

        #image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values']
        #file_handling.save_tmp_image(image_path)

        if rValue != 0:
            system.print_and_log(rValue)
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

        # block for each picture and check if an abort was requested
        if check_abort(q, dit) == -1:
            return -1

    if shutter.shutter_close() != 'CLOSED':
        system.print_and_log("Error: failed to close the shutter")

    database.store_obs_log({'sequencer_status': 'WAITING'})


def target_observation(**seq_args):
    """
    On sky target observation sequence

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
    kalfilter = seq_args.get('kalfilter')
    filepath = seq_args.get('filepath')
    dit = seq_args.get('dit')
    kao = seq_args.get('kao').upper()

    if None in (q, dit):
        system.print_and_log(
                'Missing keyword in target_observation function call')
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if core.lamps_off() != 0:
        system.print_and_log("Error: failed to turn off lamps")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if flip_mirror.down() != 'DOWN':
        system.print_and_log("Error: flip mirror did not go down")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if shutter.shutter_open() != 'OPEN':
        system.print_and_log("Error: failed to open the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if waitfortracking() == -1:
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if kalfilter is None:
        system.print_and_log(
                "Warning: no filter specified for take_image, using clear")
        kalfilter = 'clear'

    if starfinder.centre_on_target(filter_arg=kalfilter, ao=kao) == -1:
        system.print_and_log("Error: problem with centre on target")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if filterwheel.set_position(kalfilter) == -1:
        system.print_and_log("Error: problem with filter selection")
        database.store_obs_log({'sequencer_status': 'ERROR'})

        return -1

    if kao == 'AO':
        system.print_and_log("Trying to close loop")

        if aomanager.close_loop() == -1:
            system.print_and_log("Error: unable to close loop")
            database.store_obs_log({'sequencer_status': 'ERROR'})
            return -1

    image_path = file_handling.create_night_filepath()

    rValue, image_path = camera.take_image(dit=dit, filepath=image_path)

    #Monitor AO and cancel exposure if needed

    #image_path = database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values']
    #file_handling.save_tmp_image(image_path)

    if rValue != 0:
        system.print_and_log(rValue)
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if check_abort(q, dit) == -1:
        return -1

    database.store_obs_log({'sequencer_status': 'WAITING'})


def target_observation_abort():
    """
    Send abort instruction to fli camera and change sequencer status to 'WAITING'.
    :return: nothing
    """
    # two cancel are done to avoid concurrency problems
    rValue = camera.cancel()
    if (rValue != 0):
        system.print_and_log(rValue)

    time.sleep(1)

    rValue = camera.cancel()
    if (rValue != 0):
        system.print_and_log(rValue)

    database.store_obs_log({'sequencer_status': 'WAITING'})


def focusing(
        **seq_args
):  #q = None, dit = ExpTime, filepath = None, kalfilter = None, **kwargs):
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
    kalfilter = seq_args.get('kalfilter')
    filepath = seq_args.get('filepath')
    dit = seq_args.get('dit')

    if None in (q, dit):
        system.print_and_log(
                'Missing keyword in target_observation function call')
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if core.lamps_off() != 0:
        system.print_and_log("Error: failed to turn off lamps")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if flip_mirror.down() != 'DOWN':
        system.print_and_log("Error: flip mirror did not go down")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if shutter.shutter_open() != 'OPEN':
        system.print_and_log("Error: failed to open the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if waitfortracking() == -1:
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    # if starfinder.centre_on_target() == -1:
    #     system.print_and_log("Error: problem with centre on target")
    #     database.store_obs_log({'sequencer_status': 'ERROR'})
    #     return -1

    if kalfilter is None:
        #system.print_and_log("Warning: no filter specified for take image, using clear")
        kalfilter = 'clear'

    if filterwheel.set_position(kalfilter) == -1:
        system.print_and_log("Error: problem with filter selection")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    rValue = starfinder.focus_sequence(focus_points=6, focusing_dit=dit)

    if rValue != 0:
        system.print_and_log(rValue)
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    if check_abort(q, dit) == -1:
        return -1

    database.store_obs_log({'sequencer_status': 'WAITING'})


def focusing_abort():
    """
    Send abort instruction to fli camera and change sequencer status to 'WAITING'.
    :return: nothing
    """

    # TODO also send abort to focus_sequence not only to camera
    # two cancel are done to avoid concurrency problems
    rValue = camera.cancel()
    if (rValue != 0):
        system.print_and_log(rValue)

    time.sleep(1)

    rValue = camera.cancel()
    if (rValue != 0):
        system.print_and_log(rValue)

    database.store_obs_log({'sequencer_status': 'WAITING'})


def AO_loop_calibration(**seq_args):  #q = None, intensity = 0, **kwargs):
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

    q = seq_args.get('q')
    intensity = seq_args.get('intensity')

    if shutter.shutter_close() != 'CLOSED':
        system.print_and_log("Error: failed to close the shutter")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    if flip_mirror.up() != 'UP':
        system.print_and_log("Error: flip mirror did not go up")
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

    laser.set_intensity(intensity)

    # TODO core AO part missing
    #cacao.start_calib()

    laser.disable()

    database.store_obs_log({'sequencer_status': 'WAITING'})


def lamp_on(**seq_args):
    """
    Turn lamp on

    :return: nothing
    """

    q = seq_args.get('q')

    rValue = tungsten.on()
    if (rValue != 0):
        # TODO handle error
        system.print_and_log(rValue)

    database.store_obs_log({'sequencer_status': 'WAITING'})


def waitfortracking():
    """
    Waits for the telescope to be on target

    :return: 0 or 1 depending on success pointing
    """
    t0 = time.time()

    while time.time() - t0 < PointingTimeOut:
        tracking_status = database.get_latest_record(
                collection_name='obs_log',
                key='tracking_status')['tracking_status']
        if tracking_status == 'TRACKING':
            return 0
        time.sleep(PointingWaitTime)

    else:
        system.print_and_log('Error: Timeout while waiting to be on target.')

        return -1


def lamp_off():
    """
    Turn lamps off

    :return: nothing
    """

    # rValue = shutter.shutter_close()
    # if rValue != 'CLOSED':
    #     system.print_and_log("Error: failed to close the shutter "+str(rValue)})
    #     database.store_obs_log({'sequencer_status': 'ERROR'})
    #     return

    rValue = core.lamps_off()
    if rValue != 0:
        system.print_and_log("Error: failed to turn off lamps " + str(rValue))
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return

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
        system.print_and_log(rValue)

    rValue = laser.disable()
    if (rValue != 0):
        # TODO handle error
        system.print_and_log(rValue)

    rValue = shutter.shutter_close()
    if (rValue != 0):
        # TODO handle error
        system.print_and_log(rValue)

    system.print_and_log('END received moving into standby.')

    database.store_obs_log({'sequencer_status': 'WAITING'})


def check_abort(q, dit, AO=False):
    """
    Blocking function for exposition time
    Check every sec if Queue object q is empty
    if not, then an abort is required. Break the while sleep

    :param q:
    :param dit:
    :return: nothing
    """

    # TODO completely remove function if it's not needed

    if True:
        return 0

    t = 0
    t0 = kalao_time.now()

    while t < dit + SetupTime:
        t += 1
        time.sleep(1)
        print(".")
        # Check if an abort is required
        if q != None and not q.empty():
            q.get()
            # Update database
            database_updater.update_plc_monitoring()
            return -1
        if AO and aomanager.check_loop() == -1:
            return -1

        #database.get_obs_log(['fli_temporary_image_path'], 1)['fli_temporary_image_path']['values'][0]

        status_time = database.get_latest_record(
                'obs_log', key='fli_temporary_image_path')['time_utc'].replace(
                        tzinfo=datetime.timezone.utc)
        print((t0 - status_time).total_seconds())

        if (t0 - status_time).total_seconds() < 0:
            # Image has been taken. Stop looping.
            break

    return 0


def config(**seq_args):
    """
    Updates database with configuration parameters received from EDP.

    :param seq_args: dictionary of paramaters received
    :return:
    """

    q = seq_args.get('q')

    if 'host' in seq_args:
        database.store_obs_log({'t120_host': seq_args['host']})

    if 'user' in seq_args:
        database.store_obs_log({'observer_name': seq_args['user']})

    if 'email' in seq_args:
        database.store_obs_log({'observer_email': seq_args['email']})
    # host, user, email...

    return 0


commandDict = {
        "K_DARK": dark,
        "K_DARK_ABORT": dark_abort,
        "K_LMPFLT": tungsten_FLAT,
        "K_LMPFLT_ABORT": tungsten_FLAT_abort,
        "K_SKFLT": sky_FLAT,
        "K_TRGOBS": target_observation,
        "K_TRGOBS_ABORT": target_observation_abort,
        "K_LAMPON": lamp_on,
        "K_LAMPOF": lamp_off,
        "K_FOCUS": focusing,
        "K_FOCUS_ABORT": focusing_abort,
        "K_CONFIG": config,
        "K_END": end,
        #"kal_AO_loop_calibration":      AO_loop_calibration
        # "kal_dark":                     dark,
        # "kal_dark_abort":               dark_abort,
        # "kal_tungsten_FLAT":            tungsten_FLAT,
        # "kal_tungsten_FLAT_abort":      tungsten_FLAT_abort,
        # "kal_sky_FLAT":                 sky_FLAT,
        # "kal_target_observation":       target_observation,
        # "kal_target_observation_abort": target_observation_abort,
        # "kal_AO_loop_calibration":      AO_loop_calibration
}
