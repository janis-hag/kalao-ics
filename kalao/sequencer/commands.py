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
from datetime import datetime, timezone
from typing import Any

import numpy as np

from astropy.io import fits

import pytz

from kalao import database, logger, memory
from kalao.cacao import aocontrol
from kalao.hardware import (adc, calibunit, camera, dm, filterwheel,
                            flipmirror, hw_utils, laser, shutter, tungsten,
                            wfs)
from kalao.sequencer import centering, focusing, seq_utils
from kalao.sequencer.seq_utils import with_sequencer_status
from kalao.utils import exposure, fits_handling
from kalao.utils.json import KalAOJSONEncoder

from kalao.definitions.dataclasses import CalibrationPose
from kalao.definitions.enums import (AdaptiveOpticsMode, CenteringMode,
                                     FlipMirrorStatus, LaserStatus, LoopStatus,
                                     ObservationType, ReturnCode,
                                     SequencerStatus, ShutterStatus,
                                     TungstenStatus)
from kalao.definitions.exceptions import (
    AbortRequested, ADCConfigureFailed, CameraCancelFailed,
    CameraTakeImageFailed, CenteringFailed, DMNotOn, DMResetFailed,
    EMGainNotOff, FilterWheelNotInPosition, FlipMirrorNotDown, FlipMirrorNotUp,
    FocusSequenceFailed, LampsNotOff, LoopsNotClosed, LoopsNotOpen,
    MissingKeyword, SequencerException, ShutterNotClosed, ShutterNotOpen,
    SkyFlatExptimeTooHigh, SkyFlatExptimeTooLow, TrackingTimeout,
    TungstenNotInPosition, TungstenNotOn, TungstenSwitchedOff,
    WFSAcquisitionOff)

import config

encoder = KalAOJSONEncoder()


def bias(**seq_args: dict[str, Any]) -> ReturnCode:
    nbPic = seq_args.get('nbPic', 1)

    if nbPic is None:
        raise MissingKeyword

    calib_list = []
    for _ in range(nbPic):
        calib_list.append(
            CalibrationPose(type=ObservationType.BIAS, filter=None,
                            exposure_time=0.001))

    return _run_calibs(calib_list)


def bias_abort(**seq_args: dict[str, Any]) -> ReturnCode:
    return _abort()


def dark(**seq_args: dict[str, Any]) -> ReturnCode:
    exptime = seq_args.get('texp')
    nbPic = seq_args.get('nbPic', 1)

    if None in (exptime, nbPic):
        raise MissingKeyword

    calib_list = []
    for _ in range(nbPic):
        calib_list.append(
            CalibrationPose(type=ObservationType.DARK, filter=None,
                            exposure_time=exptime))

    return _run_calibs(calib_list)


def dark_abort(**seq_args: dict[str, Any]) -> ReturnCode:
    return _abort()


def tungsten_flat(**seq_args: dict[str, Any]) -> ReturnCode:
    filter_list = seq_args.get('filter_list',
                               config.Calib.Flats.default_flat_list)

    # Commented out as it is not clear what is meant to be checked
    # if None in (q):
    #     raise MissingKeyword

    calib_list = []
    for filter_name in filter_list:
        calib_list.append(
            CalibrationPose(
                type=ObservationType.LAMP_FLAT, filter=filter_name,
                exposure_time=config.Calib.Flats.
                tungsten_exptime_list[filter_name]))

    return _run_calibs(calib_list)


def tungsten_flat_abort(**seq_args: dict[str, Any]) -> ReturnCode:
    return _abort()


def sky_flat(**seq_args: dict[str, Any]) -> ReturnCode:
    filter_list = seq_args.get('filter_list',
                               config.Calib.Flats.default_flat_list)

    dt = datetime.now(timezone.utc).astimezone(
        pytz.timezone('America/Santiago'))

    if dt.hour < 12:
        reverse = True
    else:
        reverse = False

    filter_list = sorted(
        filter_list,
        key=lambda f: config.Calib.Flats.sky_evening_filters_order.index(f),
        reverse=reverse)

    calib_list = []
    for filter_name in filter_list:
        calib_list.append(
            CalibrationPose(type=ObservationType.SKY_FLAT, filter=filter_name,
                            exposure_time=np.nan))

    return _run_calibs(calib_list)


def sky_flat_abort(**seq_args: dict[str, Any]) -> ReturnCode:
    return _abort()


def target_observation(**seq_args: dict[str, Any]) -> ReturnCode:
    filter = seq_args.get('kalfilter')
    exptime = seq_args.get('texp')
    kao = seq_args.get('kao')
    auto_center = seq_args.get('centering')
    nbframes = seq_args.get('nbframes')
    roi_size = seq_args.get('windowsiz')
    mag = seq_args.get('mv')

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

        if flipmirror.down() != FlipMirrorStatus.DOWN:
            raise FlipMirrorNotDown

        if shutter.open() != ShutterStatus.OPEN:
            raise ShutterNotOpen

    # Always set filter as this may change inside an OB
    if centering_needed:
        if filterwheel.set_filter(centering_filter) != centering_filter:
            raise FilterWheelNotInPosition
    else:
        if filterwheel.set_filter(filter) != filter:
            raise FilterWheelNotInPosition

    if not ao_running:
        _wait_for_tracking()

        # Configure ADC once on target
        if adc.configure() != ReturnCode.OK:
            raise ADCConfigureFailed

        if centering_needed:
            _center_on_target(exptime=centering_exptime,
                              adaptiveoptics_mode=kao)

            if centering_filter != filter:
                # Move filter to correct position for science
                if filterwheel.set_filter(filter) != filter:
                    raise FilterWheelNotInPosition

        if kao == AdaptiveOpticsMode.ENABLED:
            logger.info('sequencer', 'Starting Adaptive Optics')

            if aocontrol.close_loops() != LoopStatus.ALL_LOOPS_ON:
                raise LoopsNotClosed

            time.sleep(config.AO.loop_stabilization_time)

    seq_utils.set_sequencer_status(SequencerStatus.EXPOSING, check_abort=True)

    image_path = camera.take_science_image(ObservationType.TARGET,
                                           exptime=exptime, nbframes=nbframes,
                                           roi_size=roi_size)

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

    if flipmirror.down() != FlipMirrorStatus.DOWN:
        raise FlipMirrorNotDown

    if shutter.open() != ShutterStatus.OPEN:
        raise ShutterNotOpen

    if filterwheel.set_filter(filter) != filter:
        raise FilterWheelNotInPosition

    _wait_for_tracking()

    # Configure ADC once on target
    if adc.configure() != ReturnCode.OK:
        raise ADCConfigureFailed

    seq_utils.set_sequencer_status(SequencerStatus.FOCUSING, check_abort=True)

    if focusing.focus_sequence(exptime=exptime) != ReturnCode.FOCUSING_OK:
        raise FocusSequenceFailed

    if shutter.close() != ShutterStatus.CLOSED:
        logger.error('sequencer',
                     'Failed to close the shutter after focus sequence')

    return ReturnCode.SEQ_OK


def focus_abort(**seq_args: dict[str, Any]) -> ReturnCode:
    return _abort()


def lamp_on(**seq_args: dict[str, Any]) -> ReturnCode:
    """
    Turn lamp on
    """
    if tungsten.on() != TungstenStatus.ON:
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
    centering.invalidate_manual_centering()

    return ReturnCode.SEQ_OK


def instrument_change(**seq_args: dict[str, Any]) -> ReturnCode:
    """
    Change of instrument operation, go into standby mode.
    """
    logger.info('sequencer', 'INSTRUMENTCHANGE received, moving into standby.')

    # Note: do NOT turn DM off (only at the end of the night)
    _open_loops()
    _shut_off_plc()
    centering.invalidate_manual_centering()

    return ReturnCode.SEQ_OK


def end(**seq_args: dict[str, Any]) -> ReturnCode:
    """
    End of instrument operation, go into standby mode and starting morning calibrations.
    """
    logger.info('sequencer', 'END received, moving into standby.')

    _open_loops()
    _shut_off_plc()
    centering.invalidate_manual_centering()

    if dm.off() != ReturnCode.OK:
        logger.warn('sequencer', 'Unable to turn off DM')

    if wfs.stop_acquisition() != ReturnCode.OK:
        logger.warn('sequencer', 'Unable to stop WFS acquisition')

    # Release Euler synchro
    seq_utils.set_sequencer_status(SequencerStatus.WAITING, check_abort=True)

    time.sleep(2)

    # Generate darks for this night

    exptimes = fits_handling.get_exposure_times_for_darks()

    if len(exptimes) == 0:
        logger.info('sequencer',
                    'Not generating darks as no science exposures found.')
        return ReturnCode.OK
    else:
        logger.info(
            'sequencer',
            f'Generating darks for {len(exptimes)} exposure times ({", ".join([f"{exptime} s" for exptime in exptimes])})'
        )

        calib_list = []
        for exptime in exptimes:
            for _ in range(config.Calib.Darks.dark_number):
                calib_list.append(
                    CalibrationPose(type=ObservationType.DARK, filter=None,
                                    exposure_time=exptime))

        return _run_calibs(calib_list)


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


def _abort() -> ReturnCode:
    centering.invalidate_manual_centering()

    if camera.cancel() != ReturnCode.OK:
        raise CameraCancelFailed

    return ReturnCode.SEQ_OK


@with_sequencer_status(SequencerStatus.WAIT_TRACKING)
def _wait_for_tracking() -> ReturnCode:
    """
    Waits for the telescope to be on target
    """
    timeout = time.monotonic() + config.Sequencer.pointing_timeout

    logger.info('sequencer', 'Waiting for telescope to be on target.')

    while time.monotonic() < timeout:
        on_target = database.get_last_value('obs', 'sequencer_on_target')

        if on_target:
            logger.info('sequencer', 'Telescope on target.')
            fits_handling.update_db_from_telheader()
            return ReturnCode.SEQ_OK

        if seq_utils.is_aborting():
            raise AbortRequested

        time.sleep(config.Sequencer.pointing_poll_interval)

    else:
        logger.error(
            'sequencer',
            'Timeout while waiting for the telescope to be on target.')
        raise TrackingTimeout


@with_sequencer_status(SequencerStatus.WAIT_LAMP)
def _wait_for_tungsten() -> ReturnCode:
    # Wait for tungsten to warm up
    state, switch_time = tungsten.get_switch_time()

    logger.info('sequencer', 'Waiting for tungsten lamp to warm up.')

    while switch_time < config.Tungsten.stabilisation_time:
        # Check if lamp is still on
        if state != TungstenStatus.ON:
            raise TungstenSwitchedOff

        if seq_utils.is_aborting():
            raise AbortRequested

        time.sleep(config.Tungsten.stabilisation_poll_interval)

        state, switch_time = tungsten.get_switch_time()

    logger.info('sequencer', 'Tungsten lamp ready.')
    return ReturnCode.SEQ_OK


@with_sequencer_status(SequencerStatus.CENTERING)
def _center_on_target(exptime, adaptiveoptics_mode):
    if centering.center_on_target(exptime=exptime,
                                  adaptiveoptics_mode=adaptiveoptics_mode
                                  ) != ReturnCode.CENTERING_OK:
        raise CenteringFailed


def _run_calibs(calib_list: list[CalibrationPose]) -> ReturnCode:
    seq_utils.set_sequencer_status(SequencerStatus.CALIBRATIONS,
                                   check_abort=True)
    memory.mset({
        'calibration_poses_timestamp': datetime.now(timezone.utc).timestamp(),
        'calibration_poses_list': encoder.encode(calib_list),
        'calibration_poses_step': 0
    })

    prev_calib_type = None
    prev_filter = filterwheel.get_filter(type=str)
    prev_exptime = None
    img = None
    step = 0

    for calib in calib_list:
        try:
            step += 1
            memory.set('calibration_poses_step', step)

            # Setup, if needed

            if prev_calib_type != calib.type:
                if calib.type == ObservationType.BIAS or calib.type == ObservationType.DARK:
                    if hw_utils.lamps_off() != ReturnCode.OK:
                        raise LampsNotOff

                    if shutter.close() != ShutterStatus.CLOSED:
                        raise ShutterNotClosed

                elif calib.type == ObservationType.LAMP_FLAT:
                    if wfs.emgain_off() != ReturnCode.OK:
                        raise EMGainNotOff

                    if dm.on() != ReturnCode.OK:
                        raise DMNotOn

                    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
                        raise LoopsNotOpen

                    if aocontrol.reset_all_dms() != ReturnCode.OK:
                        raise DMResetFailed

                    if tungsten.on() != TungstenStatus.ON:
                        raise TungstenNotOn

                    if np.isnan(calibunit.move_to_tungsten_position()):
                        raise TungstenNotInPosition

                    if shutter.close() != ShutterStatus.CLOSED:
                        raise ShutterNotClosed

                    if flipmirror.up() != FlipMirrorStatus.UP:
                        raise FlipMirrorNotUp

                    _wait_for_tungsten()

                elif calib.type == ObservationType.SKY_FLAT:
                    if wfs.emgain_off() != ReturnCode.OK:
                        raise EMGainNotOff

                    if dm.on() != ReturnCode.OK:
                        raise DMNotOn

                    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
                        raise LoopsNotOpen

                    if aocontrol.reset_all_dms() != ReturnCode.OK:
                        raise DMResetFailed

                    if hw_utils.lamps_off() != ReturnCode.OK:
                        raise LampsNotOff

                    if flipmirror.down() != FlipMirrorStatus.DOWN:
                        raise FlipMirrorNotDown

                    if shutter.open() != ShutterStatus.OPEN:
                        raise ShutterNotOpen

                    _wait_for_tracking()

                    # TODO: check sun elevation

                    prev_exptime = None

            prev_calib_type = calib.type

            # Checks that need to be done for every pose

            if calib.type == ObservationType.LAMP_FLAT:
                # Check if tungsten is still on
                if tungsten.get_status() != TungstenStatus.ON:
                    raise TungstenSwitchedOff

            elif calib.type == ObservationType.SKY_FLAT:
                if np.isnan(calib.exposure_time):
                    # Compute exposure time
                    if prev_exptime is None or img is None:
                        calib.exposure_time = exposure.flat_exptime(
                            config.Calib.Flats.target_adu, calib.filter)
                    else:
                        calib.exposure_time = exposure.next_flat_exptime(
                            config.Calib.Flats.target_adu, img, prev_exptime,
                            prev_filter, calib.filter)

                    memory.set('calibration_poses_list',
                               encoder.encode(calib_list))

                    if calib.exposure_time < config.Calib.Flats.min_exptime:
                        raise SkyFlatExptimeTooLow

                    elif calib.exposure_time > config.Calib.Flats.max_exptime:
                        raise SkyFlatExptimeTooHigh

            # Set correct filter, if needed

            if calib.filter is not None and prev_filter != calib.filter:
                if filterwheel.set_filter(calib.filter) != calib.filter:
                    raise FilterWheelNotInPosition

                prev_filter = calib.filter

            # Check if an abort was requested before taking image

            if seq_utils.is_aborting():
                raise AbortRequested

            # Prevent inactivity checks from triggering

            database.store('obs', {'deadman_keepalive': -1})

            # Take image

            logger.info(
                'sequencer',
                f'Taking image for {calib.type.name}, exposure time = {calib.exposure_time:.3f} s'
            )

            calib.status = 'EXPOSING'
            memory.set('calibration_poses_list', encoder.encode(calib_list))

            image_path = camera.take_science_image(calib.type,
                                                   exptime=calib.exposure_time)

            if image_path is None:
                raise CameraTakeImageFailed

            prev_exptime = calib.exposure_time
            img = fits.getdata(image_path)

            calib.median = np.median(img)
            calib.status = 'OK'
            memory.set('calibration_poses_list', encoder.encode(calib_list))

            # Check if an abort was requested
            if seq_utils.is_aborting():
                raise AbortRequested

        except AbortRequested as exc:
            calib.status = 'ERROR'
            memory.set('calibration_poses_list', encoder.encode(calib_list))

            raise exc

        except (SkyFlatExptimeTooHigh, SkyFlatExptimeTooLow) as exc:
            calib.status = 'SKIPPED'
            calib.error_text = exc.__doc__
            memory.set('calibration_poses_list', encoder.encode(calib_list))

            continue

        except SequencerException as exc:
            logger.error('sequencer',
                         f'"{exc.__doc__}" happened during calibration pose')

            calib.status = 'ERROR'
            calib.error_text = exc.__doc__
            memory.set('calibration_poses_list', encoder.encode(calib_list))

            continue

    # Note: do not turn off tungsten in case of successive flats

    if shutter.close() != ShutterStatus.CLOSED:
        logger.error('sequencer',
                     'Failed to close the shutter after calibration poses')

    return ReturnCode.SEQ_OK


def _open_loops() -> None:
    if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
        logger.warn('sequencer', 'Failed to open loops.')

    if wfs.emgain_off() != ReturnCode.OK:
        logger.warn('sequencer', 'Failed to turn WFS EM gain off.')

    if wfs.set_exptime(0) != ReturnCode.OK:
        logger.warn('sequencer', 'Failed to reset WFS exposure time.')

    if aocontrol.reset_all_dms() != ReturnCode.OK:
        logger.warn('sequencer', 'Failed to reset DM and TTM.')


def _shut_off_plc() -> None:
    if tungsten.off() != TungstenStatus.OFF:
        logger.warn('sequencer', 'Failed to turn off tungsten lamp.')

    if laser.disable() != LaserStatus.OFF:
        logger.warn('sequencer', 'Failed to turn off laser.')

    if shutter.close() != ShutterStatus.CLOSED:
        logger.warn('sequencer', 'Failed to close shutter.')


commands = {
    'K_BIAS': bias,
    'K_BIAS_ABORT': bias_abort,
    'K_DARK': dark,
    'K_DARK_ABORT': dark_abort,
    'K_LMPFLT': tungsten_flat,
    'K_LMPFLT_ABORT': tungsten_flat_abort,
    'K_SKYFLT': sky_flat,
    'K_SKYFLT_ABORT': sky_flat_abort,
    'K_TRGOBS': target_observation,
    'K_TRGOBS_ABORT': target_observation_abort,
    'K_LAMPON': lamp_on,
    'K_LAMPOF': lamp_off,
    'K_FOCUS': focus,
    'K_FOCUS_ABORT': focus_abort,
    'K_CONFIG': edp_config,
    'ABORT': abort,
    'OBCHANGE': ob_change,
    'INSTRUMENTCHANGE': instrument_change,
    'THE_END': end,
    'K_ENDCAL': end,
}
