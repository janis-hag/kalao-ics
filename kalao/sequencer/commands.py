#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : info.py
# @Date : 2021-01-02-16-50
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
commands.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import time

import numpy as np

from astropy.io import fits

from kalao import database, logger
from kalao.cacao import aocontrol
from kalao.fli import camera
from kalao.plc import (adc, calibunit, filterwheel, flipmirror, laser,
                       plc_utils, shutter, tungsten)
from kalao.sequencer import centering, focusing
from kalao.sequencer.seq_context import with_sequencer_status
from kalao.utils import file_handling, starfinder

from kalao.definitions.enums import (FlipMirrorPosition, LaserState,
                                     LoopStatus, ObservationType, ReturnCode,
                                     SequencerStatus, ShutterState,
                                     TungstenState)
from kalao.definitions.exceptions import *

import config


def dark(**seq_args):
    """
    :param q: Queue object for multithreads communication
    :param dit: float for exposition time
    :param nbPic: number of picture taken
    :param filepath: If filepath is not None, store the picture to this path
    :param kwargs: supports additional arguments
    :return: nothing
    """

    q = seq_args.get('q')
    dit = seq_args.get('dit')
    nbPic = seq_args.get('nbPic', 1)

    if None in (q, dit, nbPic):
        raise MissingKeyword

    if plc_utils.lamps_off() != 0:
        raise LampsNotOff

    if shutter.close() != ShutterState.CLOSED:
        raise ShutterNotClosed

    # Check if an abort was requested before taking image
    _check_abort(q)

    filepath = file_handling.generate_image_filepath()

    # Take nbPic image
    for _ in range(nbPic):
        image_path = camera.take_image(ObservationType.DARK, dit=dit,
                                       filepath=filepath)

        if image_path is None:
            raise FLITakeImageFailed

        # Check if an abort was requested
        _check_abort(q)

    return ReturnCode.SEQ_OK


def dark_abort(**seq_args):
    return _abort_camera()


def tungsten_flat(**seq_args):
    """
    :param q: Queue object for multithreads communication
    :param beck:
    :param dit: float for exposition time
    :param filepath: If filepath is not None, store the picture to this path
    :param kwargs: supports additional arguments
    :return: nothing
    """

    q = seq_args.get('q')
    filter_list = seq_args.get('filter_list', config.Calib.default_flat_list)
    filepath = seq_args.get('filepath')

    # Commented out as it is not clear what is meant to be checked
    # if None in (q):
    #     return ReturnCode.MissingKeyword

    if aocontrol.emgain_off() == -1:
        raise EMGainNotOff

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if tungsten.on() != TungstenState.ON:
        raise TungstenNotOn

    if np.isnan(calibunit.move_to_tungsten_position()):
        raise TungstenNotInPosition

    if shutter.close() != ShutterState.CLOSED:
        raise ShutterNotClosed

    if flipmirror.up() != FlipMirrorPosition.UP:
        raise FlipMirrorNotUp

    # Check if an abort was requested
    _check_abort(q)

    # if filepath is None:
    #     filepath = file_handling.create_night_filepath()
    # else:
    #     # TODO, verify that temporary_path is in the filepath
    #     temporary_path = file_handling.create_night_folder()

    _wait_for_tungsten(q)

    for filter_name in filter_list:

        # Check if lamp is still on
        if tungsten.get_state() != TungstenState.ON:
            raise TungstenSwitchedOff

        if filterwheel.set_filter(filter_name) != filter_name:
            raise FilterWheelNotInPosition

        dit = config.Tungsten.flat_dit_list[filter_name]

        image_path = file_handling.generate_image_filepath()

        image_path = camera.take_image(ObservationType.LAMP_FLAT, dit=dit,
                                       filepath=image_path)

        if image_path is None:
            raise FLITakeImageFailed

        # block for each picture and check if an abort was requested
        _check_abort(q)

    # TODO move tungsen.off() to start of other commands so that the lamp stays on if needed
    # tungsten.off()
    return ReturnCode.SEQ_OK


def tungsten_flat_abort(**seq_args):
    return _abort_camera()


def sky_flat(**seq_args):
    """
    :param q: Queue object for multithreads communication
    :param dit: float for exposition time
    :param filepath: If filepath is not None, store the picture to this path
    :param kwargs: supports additional arguments
    :return: nothing
    """

    #TODO abort sequence when flux too low

    q = seq_args.get('q')
    filter_list = seq_args.get('filter_list', config.Calib.default_flat_list)
    filepath = seq_args.get('filepath')
    dit = seq_args.get('dit')

    #if None in (q, dit, filepath):
    if q is None:
        # TODO verify which arguments are actually needed.
        raise MissingKeyword

    if aocontrol.emgain_off() == -1:
        raise EMGainNotOff

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if plc_utils.lamps_off() != 0:
        raise LampsNotOff

    if flipmirror.down() != FlipMirrorPosition.DOWN:
        raise FlipMirrorNotDown

    if shutter.open() != ShutterState.OPEN:
        raise ShutterNotOpen

    if filterwheel.set_filter(filter_list[0]) != filter_list[0]:
        raise FilterWheelNotInPosition

    # Check if an abort was requested
    _check_abort(q)

    _wait_for_tracking()

    current_filter = filter_list[0]
    dit_list = config.Tungsten.flat_dit_list

    ref_dit = optimise_dit(5, sequencer_arguments=seq_args,
                           min_flux=config.Calib.flat_min_flux)

    coef = ref_dit / dit_list[filter_list[0]]

    # Adapt integration times
    for f, d in dit_list.items():
        dit_list[f] = np.round(d * coef)

    for filter_name in filter_list:

        if filter_name != current_filter:
            current_filter = filter_name
            if filterwheel.set_filter(filter_name) != filter_name:
                raise FilterWheelNotInPosition

        #dit = optimise_dit(5, sequencer_arguments=seq_args)

        image_path = camera.take_image(ObservationType.SKY_FLAT,
                                       dit=dit_list[filter_name])

        if image_path is None:
            raise FLITakeImageFailed

        # Check if an abort was requested
        _check_abort(q)

    if shutter.close() != ShutterState.CLOSED:
        logger.error('sequencer', 'Failed to close the shutter after sky flat')

    return ReturnCode.SEQ_OK


def sky_flat_abort(**seq_args):
    return _abort_camera()


def target_observation(**seq_args):
    """
    On sky target observation sequence

    :param q: Queue object for multithreads communication
    :param dit: float for exposition time
    :param filepath: If filepath is not None, store the picture to this path
    :param kwargs: supports additional arguments
    :return: nothing
    """

    # TODO check for "'centering', 'non'"
    # TODO verify if we are already centred from previous observation

    q = seq_args.get('q')
    kalfilter = seq_args.get('kalfilter')
    filepath = seq_args.get('filepath')
    dit = seq_args.get('dit')
    kao = seq_args.get('kao').upper()
    auto_center = seq_args.get('auto_center')
    mag_v = seq_args.get('mv')

    if kalfilter is None:
        logger.warn('sequencer',
                    'No filter specified for observation, using clear')
        kalfilter = 'clear'

    # TODO
    # if auto_center == 'aut' or not database.get_last_value(
    #         'obs', 'tracking_status') == TrackingStatus.TRACKING:
    #     aocontrol.open_loops()
    #     aocontrol.reset_all_dms()

    if None in (q, dit):
        raise MissingKeyword

    #TODO: update when focusing working
    focusing.autofocus()

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if aocontrol.start_wfs_acquisition() != 0:
        raise WFSNotOn

    if plc_utils.lamps_off() != 0:
        raise LampsNotOff

    if flipmirror.down() != FlipMirrorPosition.DOWN:
        raise FlipMirrorNotDown

    if shutter.open() != ShutterState.OPEN:
        raise ShutterNotOpen

    # Put filter on clear to center on target
    if auto_center == 'aut' and filterwheel.set_filter('clear') != 'clear':
        raise FilterWheelNotInPosition

    _wait_for_tracking()

    # Configure ADC once on target
    if adc.configure() != 0:
        raise ADCConfigureFailed

    if kao == 'NO_AO':
        if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
            raise LoopsNotOpen

    if auto_center == 'aut' or kao == 'AO':
        acq_dit = config.FLI.exp_time
        if 8 < float(mag_v) < 10:
            acq_dit = 10
        if 10 < float(mag_v):
            acq_dit = 20

        if centering.center_on_target(kao=kao,
                                      dit=acq_dit) != ReturnCode.CENTERING_OK:
            raise CenteringFailed

    # Move filter to correct position for science
    if filterwheel.set_filter(kalfilter) != kalfilter:
        raise FilterWheelNotInPosition

    if kao == 'AO':
        logger.info('sequencer', 'Starting Adaptive Optics')

        # To be used and corrected if AO with manual is to be supported
        # if centering != 'aut':
        #     if starfinder.check_wfs_flux() != 0:
        #         for i in range(5):
        #             if _center_on_target(kao=kao, dit=acq_dit) == 0:
        #                 break
        #             time.sleep(3)
        #
        #     aocontrol.wfs_centering(tt_threshold=config.AO.
        #                         WFS_centering_slope_threshold)

        if aocontrol.close_loops() != LoopStatus.ALL_LOOPS_ON:
            raise LoopNotClosed

        time.sleep(config.Starfinder.AO_wait_settle)

        aocontrol.tiptilt_ttm_to_telescope(override_threshold=True)

        time.sleep(config.Starfinder.AO_wait_settle)

    image_path = file_handling.generate_image_filepath()

    image_path = camera.take_image(ObservationType.OBJECT, dit=dit,
                                   filepath=image_path)

    #Monitor AO and cancel exposure if needed

    if image_path is None:
        raise FLITakeImageFailed

    return ReturnCode.SEQ_OK


def target_observation_abort(**seq_args):
    return _abort_camera()


def focus(**seq_args):
    """
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

    if kalfilter is None:
        logger.warn('sequencer',
                    'No filter specified for focusing, using clear')
        kalfilter = 'clear'

    if q is None:
        raise MissingKeyword

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if aocontrol.reset_all_dms() != 0:
        raise DMResetFailed

    if plc_utils.lamps_off() != 0:
        raise LampsNotOff

    if flipmirror.down() != FlipMirrorPosition.DOWN:
        raise FlipMirrorNotDown

    if shutter.open() != ShutterState.OPEN:
        raise ShutterNotOpen

    _wait_for_tracking()

    # Configure ADC once on target
    if adc.configure() != 0:
        raise ADCConfigureFailed

    # if _center_on_target(kao=kao, dit=acq_dit) == -1:
    #     return ReturnCode.SEQ_CENTERING_FAILED

    # if dit is None:# in (q, dit):
    #     system.print_and_log(
    #             'No focusing dit given. Searching for optimal dit')
    #     database.store('obs',{'sequencer_status': SequencerStatus.ERROR})
    #     return -1

    if filterwheel.set_filter(kalfilter) != kalfilter:
        raise FilterWheelNotInPosition

    ret = focusing.focus_sequence(dit=dit, abort_queue=q)

    if ret != 0:
        raise FLITakeImageFailed

    return ReturnCode.SEQ_OK


def focus_abort(**seq_args):
    return _abort_camera()


def lamp_on(**seq_args):
    """
    Turn lamp on

    :return: nothing
    """

    if tungsten.on() != 0:
        raise TungstenNotOn

    return ReturnCode.SEQ_OK


def lamp_off(**seq_args):
    """
    Turn lamps off

    :return: nothing
    """

    if plc_utils.lamps_off() != 0:
        raise LampsNotOff

    return ReturnCode.SEQ_OK


def abort(**seq_args):
    return _abort_camera()


def instrument_change(**seq_args):
    """
    Change of instrument operation, go into standby mode.

    :return: nothing
    """

    logger.info('sequencer', 'INSTRUMENTCHANGE received, moving into standby.')

    # Note: do NOT turn DM off (only at the end of the night)
    _open_loops()
    _shut_off_plc()

    database.store('obs', {
        'tracking_manual_centering': False,
    })

    return ReturnCode.SEQ_OK


def stopao(**seq_args):
    """
    Change of target. Stopping AO

    :return: nothing
    """

    logger.info('sequencer', 'STOPAO received, opening loop.')

    _open_loops()

    database.store('obs', {
        'tracking_manual_centering': False,
    })

    return ReturnCode.SEQ_OK


def end(**seq_args):
    """
    End of instrument operation, go into standby mode and starting morning calibrations.

    :return: nothing
    """

    logger.info('sequencer', 'END received, moving into standby.')

    _open_loops()
    _shut_off_plc()

    database.store('obs', {
        'tracking_manual_centering': False,
    })

    if aocontrol.turn_dm_off() != ReturnCode.OK:
        logger.warn('sequencer', 'Unable to turn off DM')

    if aocontrol.stop_wfs_acquisition() != ReturnCode.OK:
        logger.warn('sequencer', 'Unable to stop WFS acquisition')

    # Release Euler synchro
    database.store('obs', {
        'sequencer_status': SequencerStatus.WAITING,
    })

    time.sleep(2)

    # Generate darks for this night
    generate_night_darks()

    return ReturnCode.SEQ_OK


def edp_config(**seq_args):
    """
    Updates database with configuration parameters received from EDP.

    :param seq_args: dictionary of paramaters received
    :return:
    """

    if 'host' in seq_args:
        database.store('obs', {'t120_host': seq_args['host']})

    if 'user' in seq_args:
        database.store('obs', {'observer_name': seq_args['user']})

    if 'email' in seq_args:
        database.store('obs', {'observer_email': seq_args['email']})

    return ReturnCode.SEQ_OK


def _check_abort(q):
    if q is not None and not q.empty():
        raise AbortRequested

    return ReturnCode.SEQ_OK


def _abort_camera():
    ret = camera.cancel()
    if ret != 0:
        raise FLICancelFailed

    return ReturnCode.SEQ_OK


def _wait_for_tracking():
    """
    Waits for the telescope to be on target

    :return: 0 or 1 depending on success pointing
    """
    timeout = time.monotonic() + config.SEQ.pointing_timeout

    while time.monotonic() < timeout:
        on_target = database.get_last_value('obs', 'sequencer_on_target')

        if on_target:
            file_handling.update_db_from_telheader()
            return ReturnCode.SEQ_OK

        time.sleep(config.SEQ.pointing_wait_time)

    else:
        logger.error(
            'sequencer',
            'Timeout while waiting for the telescope to be on target.')
        raise TrackingTimeout


@with_sequencer_status(SequencerStatus.WAITLAMP)
def _wait_for_tungsten(q):
    # Wait for tungsten to warm up
    state, switch_time = tungsten.get_switch_time()

    while switch_time < config.Tungsten.stabilisation_time:
        # Check if lamp is still on
        if state != TungstenState.ON:
            raise TungstenSwitchedOff

        _check_abort(q)

        time.sleep(config.Tungsten.switch_wait)

        state, switch_time = tungsten.get_switch_time()

    return ReturnCode.SEQ_OK


def optimise_dit(starting_dit, min_flux=config.Starfinder.min_flux,
                 max_flux=config.Starfinder.max_flux):
    """
    Search for optimal dit value to reach the requested ADU.

    TODO implement filter change to nd if dit too short.

    :return: optimal dit value
    """

    new_dit = starting_dit

    for i in range(config.Starfinder.dit_optimization_trials):

        filepath = camera.take_image(ObservationType.TECHNICAL, dit=new_dit)

        #time.sleep(20)
        file_handling.add_comment(filepath,
                                  "Dit optimisation sequence: " + str(new_dit))

        image = fits.getdata(filepath)
        # flux = image[np.argpartition(image, -6)][-6:].sum()
        #flux = np.sort(np.ravel(image))[-focusing_pixels:].sum()

        print(new_dit, image.max(), max_flux, min_flux)
        if image.mean() >= max_flux:
            new_dit = int(np.floor(max_flux / (1.5 * image.mean())))
            #new_dit = int(np.floor(0.8 * new_dit))
            if new_dit <= 1:
                print('Max flux ' + str(image.max()) +
                      ' above max permitted value ' + str(max_flux))
                return -1
            continue
        elif image.mean() <= min_flux:
            new_dit = int(np.floor(1.5 * min_flux / image.mean()))
            #new_dit = int(np.ceil(1.2 * new_dit))
            if new_dit >= config.Starfinder.max_dit:
                print('Max flux ' + str(image.max()) +
                      ' below minimum permitted value: ' + str(min_flux))
                return -1
            continue
        else:
            break

    print('Optimal dit: ' + str(new_dit))

    return new_dit


@with_sequencer_status(SequencerStatus.DARKS)
def generate_night_darks(science_folder=None):
    """
    Generate the darks needed for the calibration of the night which is assumed to have ended.
    """

    if science_folder is None:
        _, science_folder = file_handling.create_night_folders()

    exp_times = file_handling.get_exposure_times(science_folder)

    if len(exp_times) == 0:
        print(f'WARN: Not generating darks as {science_folder} is empty.')
        return 0
    else:
        for dit in exp_times:
            for i in range(config.Calib.dark_number):
                print(dit, i)  #TODO: print sequencer?
                image_path = camera.take_image(ObservationType.DARK, dit=dit)

    return 0


def _open_loops():
    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
        logger.warn('sequencer', 'Failed to open loops.')

    if aocontrol.emgain_off() != ReturnCode.OK:
        logger.warn('sequencer', 'Failed to turn WFS EM gain off.')

    if aocontrol.set_exptime(0) != ReturnCode.OK:
        logger.warn('sequencer', 'Failed to reset WFS exposure time.')


def _shut_off_plc():
    if tungsten.off() != TungstenState.OFF:
        logger.warn('sequencer', 'Failed to turn off tungsten lamp.')

    if laser.disable() != LaserState.OFF:
        logger.warn('sequencer', 'Failed to turn off laser.')

    if shutter.close() != ShutterState.CLOSED:
        logger.warn('sequencer', 'Failed to close shutter.')


commands = {
    "K_DARK": dark,
    "K_DARK_ABORT": dark_abort,
    "K_LMPFLT": tungsten_flat,
    "K_LMPFLT_ABORT": tungsten_flat_abort,
    "K_SKYFLT": sky_flat,
    "K_SKYFLT_ABORT": sky_flat_abort,
    "K_TRGOBS": target_observation,
    "K_TRGOBS_ABORT": target_observation_abort,
    "K_LAMPON": lamp_on,
    "K_LAMPOF": lamp_off,
    "K_FOCUS": focus,
    "K_FOCUS_ABORT": focus_abort,
    "K_CONFIG": edp_config,
    "ABORT": abort,
    "INSTRUMENTCHANGE": instrument_change,
    "THE_END": end,
    "K_ENDCAL": end,
    "STOPAO": stopao,
}
