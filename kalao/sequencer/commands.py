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
from typing import Any

import numpy as np

from astropy.io import fits

from kalao import database, logger
from kalao.cacao import aocontrol
from kalao.hardware import (adc, calibunit, camera, dm, filterwheel,
                            flipmirror, hw_utils, laser, shutter, tungsten,
                            wfs)
from kalao.sequencer import centering, focusing
from kalao.sequencer.seq_context import with_sequencer_status
from kalao.utils import exposure, file_handling

from kalao.definitions.enums import (AdaptiveOpticsMode, CenteringMode,
                                     FlipMirrorPosition, LaserState,
                                     LoopStatus, ObservationType, ReturnCode,
                                     SequencerStatus, ShutterState,
                                     TungstenState)
from kalao.definitions.exceptions import (
    AbortRequested, ADCConfigureFailed, CameraCancelFailed,
    CameraTakeImageFailed, CenteringFailed, DMNotOn, DMResetFailed,
    EMGainNotOff, FilterWheelNotInPosition, FlipMirrorNotDown, FlipMirrorNotUp,
    FocusSequenceFailed, LampsNotOff, LoopsNotClosed, LoopsNotOpen,
    MissingKeyword, ShutterNotClosed, ShutterNotOpen, TrackingTimeout,
    TungstenNotInPosition, TungstenNotOn, TungstenSwitchedOff,
    WFSAcquisitionOff)

import config


def dark(**seq_args: dict[str, Any]) -> ReturnCode:
    exptime = seq_args.get('texp')
    nbPic = seq_args.get('nbPic', 1)

    if None in (exptime, nbPic):
        raise MissingKeyword

    if hw_utils.lamps_off() != ReturnCode.OK:
        raise LampsNotOff

    if shutter.close() != ShutterState.CLOSED:
        raise ShutterNotClosed

    # Check if an abort was requested before taking image
    _check_abort()

    # Take darks
    for _ in range(nbPic):
        image_path = camera.take_image(ObservationType.DARK, exptime=exptime)

        if image_path is None:
            raise CameraTakeImageFailed

        # Check if an abort was requested
        _check_abort()

    return ReturnCode.SEQ_OK


def dark_abort(**seq_args: dict[str, Any]) -> ReturnCode:
    return _abort()


def tungsten_flat(**seq_args: dict[str, Any]) -> ReturnCode:
    filter_list = seq_args.get('filter_list',
                               config.Calib.Flats.default_flat_list)

    # Commented out as it is not clear what is meant to be checked
    # if None in (q):
    #     raise MissingKeyword

    if aocontrol.emgain_off() != ReturnCode.OK:
        raise EMGainNotOff

    if dm.on() != ReturnCode.OK:
        raise DMNotOn

    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
        raise LoopsNotOpen

    if aocontrol.reset_all_dms() != ReturnCode.OK:
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

        exptime = config.Tungsten.flat_exptime_list[filter_name]

        image_path = camera.take_image(ObservationType.LAMP_FLAT,
                                       exptime=exptime)

        if image_path is None:
            raise CameraTakeImageFailed

        # Check if an abort was requested
        _check_abort()

    # Note: do not turn off tungsten in case of successive flats

    return ReturnCode.SEQ_OK


def tungsten_flat_abort(**seq_args: dict[str, Any]) -> ReturnCode:
    return _abort()


def sky_flat(**seq_args: dict[str, Any]) -> ReturnCode:
    filter_list = seq_args.get('filter_list',
                               config.Calib.Flats.default_flat_list)

    if aocontrol.emgain_off() != ReturnCode.OK:
        raise EMGainNotOff

    if dm.on() != ReturnCode.OK:
        raise DMNotOn

    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
        raise LoopsNotOpen

    if aocontrol.reset_all_dms() != ReturnCode.OK:
        raise DMResetFailed

    if hw_utils.lamps_off() != ReturnCode.OK:
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

    exptime = exposure.flat_exptime(config.Calib.Flats.target_adu,
                                    current_filter)

    img = None

    for filter in filter_list:
        if img is not None:
            exptime = exposure.next_flat_exptime(config.Calib.Flats.target_adu,
                                                 img, exptime, current_filter,
                                                 filter)

        if exptime < config.Calib.Flats.min_exptime:
            logger.error('sequencer',
                         'Sky flat sequence stopped, exposure time too short')
            break

        if exptime > config.Calib.Flats.max_exptime:
            logger.error('sequencer',
                         'Sky flat sequence stopped, exposure time too long')
            break

        if filter != current_filter:
            if filterwheel.set_filter(filter) != filter:
                raise FilterWheelNotInPosition

            current_filter = filter

        image_path = camera.take_image(ObservationType.SKY_FLAT,
                                       exptime=exptime)

        if image_path is None:
            raise CameraTakeImageFailed

        img = fits.getdata(image_path)

        # Check if an abort was requested
        _check_abort()

    if shutter.close() != ShutterState.CLOSED:
        logger.error('sequencer', 'Failed to close the shutter after sky flat')

    return ReturnCode.SEQ_OK


def sky_flat_abort(**seq_args: dict[str, Any]) -> ReturnCode:
    return _abort()


def target_observation(**seq_args: dict[str, Any]) -> ReturnCode:
    filter = seq_args.get('kalfilter')
    exptime = seq_args.get('texp')
    kao = seq_args.get('kao').upper()
    auto_center = seq_args.get('centering')
    nbframes = seq_args.get('nbframes')
    roi_size = seq_args.get('windowsiz')
    mag = seq_args.get('mv')

    if filter is None:
        logger.warn('sequencer',
                    'No filter specified for observation, using clear')
        filter = 'clear'

    if roi_size is not None:
        roi_size = int(roi_size.split('x')[0])

    centering_exptime, centering_filter = exposure.optimal_exposure_time_and_filter(
        mag, config.Centering.min_exptime)

    ao_running = aocontrol.check_loops() == LoopStatus.ALL_LOOPS_ON

    # Do not center if AO is running, as the AO kept the target centered
    centering_needed = not ao_running and auto_center != CenteringMode.NONE

    if not ao_running:
        # Do not do a focus while AO is running (it will break the loop)
        focusing.autofocus()

        if dm.on() != ReturnCode.OK:
            raise DMNotOn

        if kao == AdaptiveOpticsMode.ENABLED:
            if wfs.start_acquisition() != ReturnCode.OK:
                raise WFSAcquisitionOff
        else:
            if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
                raise LoopsNotOpen

            if aocontrol.reset_all_dms() != ReturnCode.OK:
                raise DMResetFailed

        if hw_utils.lamps_off() != ReturnCode.OK:
            raise LampsNotOff

        if flipmirror.down() != FlipMirrorPosition.DOWN:
            raise FlipMirrorNotDown

        if shutter.open() != ShutterState.OPEN:
            raise ShutterNotOpen

    # Always set filter as this may change inside an OB
    if centering_needed:
        if filterwheel.set_filter(centering_filter) != centering_filter:
            raise FilterWheelNotInPosition
    else:
        if filterwheel.set_filter(filter) != filter:
            raise FilterWheelNotInPosition

    _wait_for_tracking()

    # Configure ADC once on target
    if adc.configure() != ReturnCode.OK:
        raise ADCConfigureFailed

    if centering_needed:
        if centering.center_on_target(
                exptime=centering_exptime,
                adaptiveoptics_mode=kao) != ReturnCode.CENTERING_OK:
            raise CenteringFailed

        if centering_filter != filter:
            # Move filter to correct position for science
            if filterwheel.set_filter(filter) != filter:
                raise FilterWheelNotInPosition

    if kao == AdaptiveOpticsMode.ENABLED and not ao_running:
        logger.info('sequencer', 'Starting Adaptive Optics')

        if aocontrol.close_loops() != LoopStatus.ALL_LOOPS_ON:
            raise LoopsNotClosed

        time.sleep(config.AO.loop_stabilization_time)

    image_path = camera.take_image(ObservationType.TARGET, exptime=exptime,
                                   nbframes=nbframes, roi_size=roi_size)

    if image_path is None:
        raise CameraTakeImageFailed

    # Note: do not close shutter in case of successive exposures

    return ReturnCode.SEQ_OK


def target_observation_abort(**seq_args: dict[str, Any]) -> ReturnCode:
    return _abort()


def focus(**seq_args: dict[str, Any]) -> ReturnCode:
    filter = seq_args.get('kalfilter')
    exptime = seq_args.get('texp')
    mag = seq_args.get('mv')

    if filter is None:
        logger.warn('sequencer',
                    'No filter specified for focusing, using clear')
        filter = 'clear'

    if exptime <= 0:
        exptime, filter = exposure.optimal_exposure_time_and_filter(
            mag, config.Focusing.min_exptime)

    if dm.on() != ReturnCode.OK:
        raise DMNotOn

    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
        raise LoopsNotOpen

    if aocontrol.reset_all_dms() != ReturnCode.OK:
        raise DMResetFailed

    if hw_utils.lamps_off() != ReturnCode.OK:
        raise LampsNotOff

    if flipmirror.down() != FlipMirrorPosition.DOWN:
        raise FlipMirrorNotDown

    if shutter.open() != ShutterState.OPEN:
        raise ShutterNotOpen

    if filterwheel.set_filter(filter) != filter:
        raise FilterWheelNotInPosition

    _wait_for_tracking()

    # Configure ADC once on target
    if adc.configure() != ReturnCode.OK:
        raise ADCConfigureFailed

    if focusing.focus_sequence(exptime=exptime) != ReturnCode.FOCUSING_OK:
        raise FocusSequenceFailed

    if shutter.close() != ShutterState.CLOSED:
        logger.error('sequencer',
                     'Failed to close the shutter after focus sequence')

    return ReturnCode.SEQ_OK


def focus_abort(**seq_args: dict[str, Any]) -> ReturnCode:
    return _abort()


def lamp_on(**seq_args: dict[str, Any]) -> ReturnCode:
    """
    Turn lamp on
    """

    if tungsten.on() != TungstenState.ON:
        raise TungstenNotOn

    return ReturnCode.SEQ_OK


def lamp_off(**seq_args: dict[str, Any]) -> ReturnCode:
    """
    Turn lamps off
    """

    if hw_utils.lamps_off() != ReturnCode.OK:
        raise LampsNotOff

    return ReturnCode.SEQ_OK


def abort(**seq_args: dict[str, Any]) -> ReturnCode:
    return _abort()


def ob_change(**seq_args: dict[str, Any]) -> ReturnCode:
    """
    Change of target. Stopping AO
    """

    logger.info('sequencer', 'OBCHANGE received, opening loop.')

    _open_loops()

    database.store('obs', {'centering_manual': False})

    return ReturnCode.SEQ_OK


def instrument_change(**seq_args: dict[str, Any]) -> ReturnCode:
    """
    Change of instrument operation, go into standby mode.
    """

    logger.info('sequencer', 'INSTRUMENTCHANGE received, moving into standby.')

    # Note: do NOT turn DM off (only at the end of the night)
    _open_loops()
    _shut_off_plc()

    database.store('obs', {'centering_manual': False})

    return ReturnCode.SEQ_OK


def end(**seq_args: dict[str, Any]) -> ReturnCode:
    """
    End of instrument operation, go into standby mode and starting morning calibrations.
    """

    logger.info('sequencer', 'END received, moving into standby.')

    _open_loops()
    _shut_off_plc()

    database.store('obs', {'centering_manual': False})

    if dm.off() != ReturnCode.OK:
        logger.warn('sequencer', 'Unable to turn off DM')

    if wfs.stop_acquisition() != ReturnCode.OK:
        logger.warn('sequencer', 'Unable to stop WFS acquisition')

    # Release Euler synchro
    database.store('obs', {
        'sequencer_status': SequencerStatus.WAITING,
    })

    time.sleep(2)

    # Generate darks for this night
    generate_night_darks()

    return ReturnCode.SEQ_OK


def edp_config(**seq_args: dict[str, Any]) -> ReturnCode:
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


def _check_abort() -> ReturnCode:
    if database.get_last_value('obs',
                               'sequencer_status') == SequencerStatus.ABORTING:
        raise AbortRequested

    return ReturnCode.SEQ_OK


def _abort() -> ReturnCode:
    database.store('obs', {'centering_manual': False})

    if camera.cancel() != ReturnCode.OK:
        raise CameraCancelFailed

    return ReturnCode.SEQ_OK


def _wait_for_tracking() -> ReturnCode:
    """
    Waits for the telescope to be on target
    """
    timeout = time.monotonic() + config.SEQ.pointing_timeout

    logger.info('sequencer', 'Waiting for telescope to be on target.')

    while time.monotonic() < timeout:
        on_target = database.get_last_value('obs', 'sequencer_on_target')

        if on_target:
            logger.info('sequencer', 'Telescope on target.')
            file_handling.update_db_from_telheader()
            return ReturnCode.SEQ_OK

        time.sleep(config.SEQ.pointing_poll_interval)

    else:
        logger.error(
            'sequencer',
            'Timeout while waiting for the telescope to be on target.')
        raise TrackingTimeout


@with_sequencer_status(SequencerStatus.WAITLAMP)
def _wait_for_tungsten() -> ReturnCode:
    # Wait for tungsten to warm up
    state, switch_time = tungsten.get_switch_time()

    logger.info('sequencer', 'Waiting for tungsten lamp to warm up.')

    while switch_time < config.Tungsten.stabilisation_time:
        # Check if lamp is still on
        if state != TungstenState.ON:
            raise TungstenSwitchedOff

        _check_abort()

        time.sleep(config.Tungsten.stabilisation_poll_interval)

        state, switch_time = tungsten.get_switch_time()

    logger.info('sequencer', 'Tungsten lamp ready.')
    return ReturnCode.SEQ_OK


@with_sequencer_status(SequencerStatus.DARKS)
def generate_night_darks(folder=None) -> ReturnCode:
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
            f'Generating {len(exptimes)} darks ({", ".join(str(exptime) for exptime in exptimes)})'
        )
        for exptime in exptimes:
            for i in range(config.Calib.Darks.dark_number):
                logger.info(
                    'sequencer',
                    f'Generating dark for {exptime} s ({i}/{config.Calib.Darks.dark_number}'
                )
                camera.take_image(ObservationType.DARK, exptime=exptime)

    return 0


def _open_loops() -> None:
    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
        logger.warn('sequencer', 'Failed to open loops.')

    if aocontrol.emgain_off() != ReturnCode.OK:
        logger.warn('sequencer', 'Failed to turn WFS EM gain off.')

    if aocontrol.set_exptime(0) != ReturnCode.OK:
        logger.warn('sequencer', 'Failed to reset WFS exposure time.')

    if aocontrol.reset_all_dms() != ReturnCode.OK:
        logger.warn('sequencer', 'Failed to reset DM and TTM.')


def _shut_off_plc() -> None:
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
    "OBCHANGE": ob_change,
    "INSTRUMENTCHANGE": instrument_change,
    "THE_END": end,
    "K_ENDCAL": end,
}
