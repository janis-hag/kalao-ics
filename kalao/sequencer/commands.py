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
from kalao.utils import exposure, file_handling

from kalao.definitions.enums import (AdaptiveOpticsMode, CenteringMode,
                                     FlipMirrorPosition, LaserState,
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

    dit = seq_args.get('dit')
    nbPic = seq_args.get('nbPic', 1)

    if None in (dit, nbPic):
        raise MissingKeyword

    if plc_utils.lamps_off() != 0:
        raise LampsNotOff

    if shutter.close() != ShutterState.CLOSED:
        raise ShutterNotClosed

    # Check if an abort was requested before taking image
    _check_abort()

    # Take darks
    for _ in range(nbPic):
        image_path = camera.take_image(ObservationType.DARK, dit=dit)

        if image_path is None:
            raise FLITakeImageFailed

        # Check if an abort was requested
        _check_abort()

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

    filter_list = seq_args.get('filter_list',
                               config.Calib.Flats.default_flat_list)
    filepath = seq_args.get('filepath')

    # Commented out as it is not clear what is meant to be checked
    # if None in (q):
    #     return ReturnCode.MissingKeyword

    if aocontrol.emgain_off() == -1:
        raise EMGainNotOff

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
        raise LoopsNotOpen

    if aocontrol.reset_all_dms() != 0:
        raise DMResetFailed

    if tungsten.on() != TungstenState.ON:
        raise TungstenNotOn

    if np.isnan(calibunit.move_to_tungsten_position()):
        raise TungstenNotInPosition

    if shutter.close() != ShutterState.CLOSED:
        raise ShutterNotClosed

    if flipmirror.up() != FlipMirrorPosition.UP:
        raise FlipMirrorNotUp

    _wait_for_tungsten()

    # Check if an abort was requested
    _check_abort()

    for filter_name in filter_list:

        # Check if lamp is still on
        if tungsten.get_state() != TungstenState.ON:
            raise TungstenSwitchedOff

        if filterwheel.set_filter(filter_name) != filter_name:
            raise FilterWheelNotInPosition

        dit = config.Tungsten.flat_dit_list[filter_name]

        image_path = camera.take_image(ObservationType.LAMP_FLAT, dit=dit)

        if image_path is None:
            raise FLITakeImageFailed

        # Check if an abort was requested
        _check_abort()

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

    filter_list = seq_args.get('filter_list',
                               config.Calib.Flats.default_flat_list)
    filepath = seq_args.get('filepath')
    dit = seq_args.get('dit')

    if aocontrol.emgain_off() == -1:
        raise EMGainNotOff

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
        raise LoopsNotOpen

    if aocontrol.reset_all_dms() != 0:
        raise DMResetFailed

    if plc_utils.lamps_off() != 0:
        raise LampsNotOff

    if flipmirror.down() != FlipMirrorPosition.DOWN:
        raise FlipMirrorNotDown

    if shutter.open() != ShutterState.OPEN:
        raise ShutterNotOpen

    if filterwheel.set_filter(filter_list[0]) != filter_list[0]:
        raise FilterWheelNotInPosition

    # Check if an abort was requested
    _check_abort()

    _wait_for_tracking()

    current_filter = filter_list[0]

    dit = exposure.flat_exptime(config.Calib.Flats.target_adu, current_filter)

    img = None

    for filter in filter_list:
        if img is not None:
            dit = exposure.next_flat_exptime(config.Calib.Flats.target_adu,
                                             img, dit, current_filter, filter)

        if dit < config.Calib.Flats.min_exptime:
            logger.error('sequencer',
                         'Sky flat sequence stopped, exposure time too short')
            break

        if dit > config.Calib.Flats.max_exptime:
            logger.error('sequencer',
                         'Sky flat sequence stopped, exposure time too long')
            break

        if filter != current_filter:
            if filterwheel.set_filter(filter) != filter:
                raise FilterWheelNotInPosition

            current_filter = filter

        image_path = camera.take_image(ObservationType.SKY_FLAT, dit=dit)

        if image_path is None:
            raise FLITakeImageFailed

        img = fits.getdata(image_path)

        # Check if an abort was requested
        _check_abort()

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

    kalfilter = seq_args.get('kalfilter')
    filepath = seq_args.get('filepath')
    dit = seq_args.get('dit')
    kao = seq_args.get('kao').upper()
    auto_center = seq_args.get('auto_center')
    mag = seq_args.get('mv')

    if kalfilter is None:
        logger.warn('sequencer',
                    'No filter specified for observation, using clear')
        kalfilter = 'clear'

    centering_exptime, centering_filter = exposure.optimal_exposure_time_and_filter(
        mag)

    ao_running = aocontrol.check_loops() == LoopStatus.ALL_LOOPS_ON

    # Do not center if AO is running, as the AO kept the target centered
    centering_needed = not ao_running and auto_center != CenteringMode.NONE

    # Do not do a focus while AO is running (it will break the loop)
    if not ao_running:
        focusing.autofocus()

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if kao == AdaptiveOpticsMode.DISABLED:
        if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
            raise LoopsNotOpen

        if aocontrol.reset_all_dms() != 0:
            raise DMResetFailed

    if aocontrol.start_wfs_acquisition() != 0:
        raise WFSNotOn

    if plc_utils.lamps_off() != 0:
        raise LampsNotOff

    if flipmirror.down() != FlipMirrorPosition.DOWN:
        raise FlipMirrorNotDown

    if shutter.open() != ShutterState.OPEN:
        raise ShutterNotOpen

    if centering_needed:
        if filterwheel.set_filter(centering_filter) != centering_filter:
            raise FilterWheelNotInPosition
    else:
        if filterwheel.set_filter(kalfilter) != kalfilter:
            raise FilterWheelNotInPosition

    _wait_for_tracking()

    # Configure ADC once on target
    if adc.configure() != 0:
        raise ADCConfigureFailed

    if centering_needed:
        if centering.center_on_target(
                dit=centering_exptime,
                adaptiveoptics_mode=kao) != ReturnCode.CENTERING_OK:
            raise CenteringFailed

    # Move filter to correct position for science
    if filterwheel.set_filter(kalfilter) != kalfilter:
        raise FilterWheelNotInPosition

    if kao == AdaptiveOpticsMode.ENABLED:
        logger.info('sequencer', 'Starting Adaptive Optics')

        if aocontrol.close_loops() != LoopStatus.ALL_LOOPS_ON:
            raise LoopNotClosed

        time.sleep(config.AO.settling_time)

    image_path = camera.take_image(ObservationType.OBJECT, dit=dit)

    #Monitor AO and cancel exposure if needed

    if image_path is None:
        raise FLITakeImageFailed

    # Do not close shutter in case of successive exposures

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

    filter = seq_args.get('kalfilter')
    filepath = seq_args.get('filepath')
    dit = seq_args.get('dit')
    mag = seq_args.get('mv')

    if filter is None:
        logger.warn('sequencer',
                    'No filter specified for focusing, using clear')
        filter = 'clear'

    if dit <= 0:
        exptime, filter = exposure.optimal_exposure_time_and_filter(mag)
        dit = exptime

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
        raise LoopsNotOpen

    if aocontrol.reset_all_dms() != 0:
        raise DMResetFailed

    if plc_utils.lamps_off() != 0:
        raise LampsNotOff

    if flipmirror.down() != FlipMirrorPosition.DOWN:
        raise FlipMirrorNotDown

    if shutter.open() != ShutterState.OPEN:
        raise ShutterNotOpen

    if filterwheel.set_filter(filter) != filter:
        raise FilterWheelNotInPosition

    _wait_for_tracking()

    # Configure ADC once on target
    if adc.configure() != 0:
        raise ADCConfigureFailed

    if focusing.focus_sequence(dit=dit) != ReturnCode.FOCUSING_OK:
        raise FocusSequenceFailed

    if shutter.close() != ShutterState.CLOSED:
        logger.error('sequencer',
                     'Failed to close the shutter after focus sequence')

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
        'centering_manual': False,
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
        'centering_manual': False,
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
        'centering_manual': False,
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


def _check_abort():
    if database.get_last_value('sequencer_status') == SequencerStatus.ABORTING:
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

        time.sleep(config.SEQ.pointing_poll_interval)

    else:
        logger.error(
            'sequencer',
            'Timeout while waiting for the telescope to be on target.')
        raise TrackingTimeout


@with_sequencer_status(SequencerStatus.WAITLAMP)
def _wait_for_tungsten():
    # Wait for tungsten to warm up
    state, switch_time = tungsten.get_switch_time()

    while switch_time < config.Tungsten.stabilisation_time:
        # Check if lamp is still on
        if state != TungstenState.ON:
            raise TungstenSwitchedOff

        _check_abort()

        time.sleep(config.Tungsten.stabilisation_poll_interval)

        state, switch_time = tungsten.get_switch_time()

    return ReturnCode.SEQ_OK


@with_sequencer_status(SequencerStatus.DARKS)
def generate_night_darks(folder=None):
    """
    Generate the darks needed for the calibration of the night which is assumed to have ended.
    """

    exptimes = file_handling.get_exposure_times()

    if len(exptimes) == 0:
        logger.warn('sequencer', f'Not generating darks as {folder} is empty.')
        return 0
    else:
        logger.info(
            'sequencer',
            f'Generating {len(exptimes)} darks ({", ".join(str(dit) for dit in [1,3.5,3])})'
        )
        for dit in exptimes:
            for i in range(config.Calib.Darks.dark_number):
                logger.info(
                    'sequencer',
                    f'Generating dark for {dit} s ({i}/{config.Calib.Darks.dark_number}'
                )
                camera.take_image(ObservationType.DARK, dit=dit)

    return 0


def _open_loops():
    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
        logger.warn('sequencer', 'Failed to open loops.')

    if aocontrol.emgain_off() != ReturnCode.OK:
        logger.warn('sequencer', 'Failed to turn WFS EM gain off.')

    if aocontrol.set_exptime(0) != ReturnCode.OK:
        logger.warn('sequencer', 'Failed to reset WFS exposure time.')

    if aocontrol.reset_all_dms() != 0:
        logger.warn('sequencer', 'Failed to reset DM and TTM.')


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
