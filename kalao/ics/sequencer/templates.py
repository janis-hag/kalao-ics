#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : info.py
# @Date : 2021-01-02-16-50
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
templates.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""
import time
import zoneinfo
from datetime import datetime, timezone
from typing import Any

import numpy as np

from astropy.io import fits

from kalao.common.dataclasses import CalibrationPose, Template
from kalao.common.enums import (AdaptiveOpticsMode, CenteringMode,
                                FlipMirrorStatus, LaserStatus, LoopStatus,
                                ReturnCode, SequencerStatus, ShutterStatus,
                                TemplateID, TungstenStatus, WindowHint)
from kalao.common.exceptions import (
    AbortRequested, ADCConfigureFailed, CameraTakeImageFailed, CenteringFailed,
    DMNotOn, DMResetFailed, EMGainNotOff, FilterWheelNotInPosition,
    FlipMirrorNotDown, FlipMirrorNotUp, LampsNotOff, LoopsNotClosed,
    LoopsNotOpen, MissingKeyword, SequencerException, ShutterNotClosed,
    ShutterNotOpen, SkyFlatExptimeTooHigh, SkyFlatExptimeTooLow,
    TrackingTimeout, TungstenNotInPosition, TungstenNotOn, TungstenSwitchedOff,
    WFSAcquisitionOff)
from kalao.common.json import KalAOJSONEncoder

from kalao.ics import database, logger, memory
from kalao.ics.cacao import aocontrol
from kalao.ics.hardware import (adc, calibunit, camera, dm, filterwheel,
                                flipmirror, hw_utils, laser, shutter, tungsten,
                                wfs)
from kalao.ics.sequencer import centering, focusing, seq_utils
from kalao.ics.sequencer.seq_utils import (SequencerStatusContextManager,
                                           WindowHintContextManager)
from kalao.ics.utils import exposure, fits_handling

import config

encoder = KalAOJSONEncoder()


def KAO_SLFTST(template, **template_args: Any) -> ReturnCode:
    try:
        exptime = template_args['texp']
    except KeyError as exc:
        raise MissingKeyword(*exc.args)

    # Simulate setup time
    time.sleep(10)

    seq_utils.set_sequencer_status(SequencerStatus.EXPOSING, check_abort=True)

    for expno in range(template.nexp):
        start = time.monotonic()

        image_path = camera.take_science_image(template, exptime=exptime)

        while time.monotonic() < start + exptime:
            time.sleep(0.1)

            if seq_utils.is_aborting():
                raise AbortRequested

        if image_path is None:
            raise CameraTakeImageFailed

        if seq_utils.is_aborting():
            raise AbortRequested

    return ReturnCode.SEQ_OK


def KAO_BIAS(template, **template_args: Any) -> ReturnCode:
    calib_list = []
    for expno in range(template.nexp):
        calib_list.append(
            CalibrationPose(template=template, filter=None,
                            exposure_time=0.001))

    return _run_calibs(calib_list)


def KAO_DARK(template, **template_args: Any) -> ReturnCode:
    try:
        exptime = template_args['texp']
    except KeyError as exc:
        raise MissingKeyword(*exc.args)

    calib_list = []
    for expno in range(template.nexp):
        calib_list.append(
            CalibrationPose(template=template, filter=None,
                            exposure_time=exptime))

    return _run_calibs(calib_list)


def KAO_LMPFLT(template, **template_args: Any) -> ReturnCode:
    filter_list = template_args.get('filter_list',
                                    config.Calib.Flats.default_flat_list)

    template.nexp = len(filter_list)

    calib_list = []
    for expno, filter_name in enumerate(filter_list):
        calib_list.append(
            CalibrationPose(
                template=template, filter=filter_name, exposure_time=config.
                Calib.Flats.tungsten_exptime_list[filter_name]))

    return _run_calibs(calib_list)


def KAO_SKYFLT(template, **template_args: Any) -> ReturnCode:
    filter_list = template_args.get('filter_list',
                                    config.Calib.Flats.default_flat_list)

    dt = datetime.now(zoneinfo.ZoneInfo('America/Santiago'))

    if dt.hour < 12:
        reverse = True
    else:
        reverse = False

    filter_list = sorted(
        filter_list,
        key=lambda f: config.Calib.Flats.sky_evening_filters_order.index(f),
        reverse=reverse)

    template.nexp = len(filter_list)

    calib_list = []
    for expno, filter_name in enumerate(filter_list):
        calib_list.append(
            CalibrationPose(template=template, filter=filter_name,
                            exposure_time=np.nan))

    return _run_calibs(calib_list)


def KAO_TRGOBS(template, **template_args: Any) -> ReturnCode:
    try:
        filter = template_args['kalfilter']
        exptime = template_args['texp']
        ao_mode = template_args['kao']
        centering_mode = template_args['centering']
        nbframes = template_args['nbframes']
        roi_size = template_args['windowsiz']
        mag = template_args['mv']
    except KeyError as exc:
        raise MissingKeyword(*exc.args)

    if roi_size is not None:
        roi_size = int(roi_size.split('x')[0])

    centering_exptime, centering_filter = exposure.optimal_exposure_time_and_filter(
        mag, config.Centering.min_exptime)

    ao_running = aocontrol.check_loops() == LoopStatus.ALL_LOOPS_ON

    # Do not center if AO is running, as the AO kept the target centered
    centering_needed = not ao_running and centering_mode != CenteringMode.NONE

    if not ao_running:
        # Do not do a focus while AO is running (it will break the loop)
        focusing.autofocus()

        if dm.on() != ReturnCode.OK:
            raise DMNotOn

        if ao_mode == AdaptiveOpticsMode.ENABLED:
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
                              adaptiveoptics_mode=ao_mode)

            # Reset sequencer status after centering
            template.to_memory()

            if centering_filter != filter:
                # Move filter to correct position for science
                if filterwheel.set_filter(filter) != filter:
                    raise FilterWheelNotInPosition

        if ao_mode == AdaptiveOpticsMode.ENABLED:
            logger.info('sequencer', 'Starting Adaptive Optics')

            if aocontrol.close_loops() != LoopStatus.ALL_LOOPS_ON:
                raise LoopsNotClosed

            with SequencerStatusContextManager(
                    SequencerStatus.WAIT_STABILISATION):
                logger.info(
                    'sequencer',
                    f'Waiting for AO loops stabilisation ({config.AO.loops_stabilization_time} s).'
                )
                time.sleep(config.AO.loops_stabilization_time)

    seq_utils.set_sequencer_status(SequencerStatus.EXPOSING, check_abort=True)

    for expno in range(template.nexp):
        image_path = camera.take_science_image(template, exptime=exptime,
                                               nbframes=nbframes,
                                               roi_size=roi_size)

        if image_path is None:
            raise CameraTakeImageFailed

        if seq_utils.is_aborting():
            raise AbortRequested

    # Note: do not close shutter in case of successive exposures

    return ReturnCode.SEQ_OK


def KAO_FOCUS(template, **template_args: Any) -> ReturnCode:
    try:
        filter = template_args['kalfilter']
        exptime = template_args['texp']
        mag = template_args['mv']
    except KeyError as exc:
        raise MissingKeyword(*exc.args)

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

    focusing.focus_sequence(template, exptime=exptime)

    if shutter.close() != ShutterStatus.CLOSED:
        logger.error('sequencer',
                     'Failed to close the shutter after focus sequence')

    return ReturnCode.SEQ_OK


def KAO_LAMPON(template, **template_args: Any) -> ReturnCode:
    """
    Turn lamp on
    """
    if tungsten.on() != TungstenStatus.ON:
        raise TungstenNotOn

    return ReturnCode.SEQ_OK


def KAO_LAMPOF(template, **template_args: Any) -> ReturnCode:
    """
    Turn lamps off
    """
    if hw_utils.lamps_off() != ReturnCode.OK:
        raise LampsNotOff

    return ReturnCode.SEQ_OK


def OBCHANGE(template, **template_args: Any) -> ReturnCode:
    """
    Change of target. Stopping AO
    """
    logger.info('sequencer', 'OBCHANGE received, opening loop.')

    _open_loops()
    centering.invalidate_manual_centering()
    database.store('obs', {'sequencer_on_target': False})

    return ReturnCode.SEQ_OK


def INSTRUMENTCHANGE(template, **template_args: Any) -> ReturnCode:
    """
    Change of instrument operation, go into standby mode.
    """
    logger.info('sequencer', 'INSTRUMENTCHANGE received, moving into standby.')

    # Note: do NOT turn DM off (only at the end of the night)
    _open_loops()
    _shut_off_plc()
    centering.invalidate_manual_centering()
    database.store('obs', {'sequencer_on_target': False})

    return ReturnCode.SEQ_OK


def KAO_ENDCAL(template, **template_args: Any) -> ReturnCode:
    """
    End of instrument operation, go into standby mode and starting morning calibrations.
    """
    logger.info('sequencer', 'END received, moving into standby.')

    _open_loops()
    _shut_off_plc()
    centering.invalidate_manual_centering()
    database.store('obs', {'sequencer_on_target': False})

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
            template = Template(id=TemplateID.DARK, start=None,
                                nexp=config.Calib.Darks.dark_number)

            for expno in range(template.nexp):
                calib_list.append(
                    CalibrationPose(template=template, filter=None,
                                    exposure_time=exptime))

        return _run_calibs(calib_list)


def KAO_CONFIG(template, **template_args: Any) -> ReturnCode:
    """
    Updates database with configuration parameters received from EDP.

    :param template_args: dictionary of paramaters received
    :return:
    """
    if 'host' in template_args:
        database.store('obs', {'t120_host': template_args['host']})

    if 'user' in template_args:
        database.store('obs', {'observer_name': template_args['user']})

    if 'email' in template_args:
        database.store('obs', {'observer_email': template_args['email']})

    return ReturnCode.SEQ_OK


def _wait_for_tracking() -> ReturnCode:
    """
    Waits for the telescope to be on target
    """
    on_target = database.get_last_value('obs', 'sequencer_on_target')

    if on_target:
        return ReturnCode.SEQ_OK

    with SequencerStatusContextManager(SequencerStatus.WAIT_TRACKING):
        timeout = time.monotonic() + config.Sequencer.pointing_timeout

        logger.info(
            'sequencer',
            f'Waiting for telescope to be on target (max. {config.Sequencer.pointing_timeout} s).'
        )

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


def _wait_for_tungsten() -> ReturnCode:
    # Wait for tungsten to warm up
    state, switch_time = tungsten.get_switch_time()

    if switch_time > config.Tungsten.stabilisation_time:
        return ReturnCode.SEQ_OK

    with SequencerStatusContextManager(SequencerStatus.WAIT_LAMP):
        logger.info(
            'sequencer',
            f'Waiting for tungsten lamp to warm up (max. {config.Tungsten.stabilisation_time} s).'
        )

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


def _center_on_target(exptime: float,
                      adaptiveoptics_mode: AdaptiveOpticsMode) -> None:
    with SequencerStatusContextManager(SequencerStatus.CENTERING):
        if centering.center_on_target(exptime=exptime,
                                      adaptiveoptics_mode=adaptiveoptics_mode
                                      ) != ReturnCode.CENTERING_OK:
            raise CenteringFailed


def _run_calibs(calib_list: list[CalibrationPose]) -> ReturnCode:
    memory.hset('calibration_poses', 'list', encoder.encode(calib_list))

    with WindowHintContextManager(WindowHint.CALIBRATION_POSES):
        prev_calib_type = None
        prev_filter = filterwheel.get_filter(type=str)
        prev_exptime = None
        img = None

        for calib in calib_list:
            try:
                if calib.template.start is None:
                    calib.template.start = datetime.now(timezone.utc)
                    calib.template.to_memory()

                # Setup, if needed

                if prev_calib_type != calib.template.id:
                    seq_utils.set_sequencer_status(SequencerStatus.SETUP,
                                                   check_abort=True,
                                                   check_status=True)

                    if calib.template.id == TemplateID.BIAS or calib.template.id == TemplateID.DARK:
                        if hw_utils.lamps_off() != ReturnCode.OK:
                            raise LampsNotOff

                        if shutter.close() != ShutterStatus.CLOSED:
                            raise ShutterNotClosed

                    elif calib.template.id == TemplateID.LAMP_FLAT:
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

                    elif calib.template.id == TemplateID.SKY_FLAT:
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

                prev_calib_type = calib.template.id

                # Checks that need to be done for every pose

                if calib.template.id == TemplateID.LAMP_FLAT:
                    # Check if tungsten is still on
                    if tungsten.get_status() != TungstenStatus.ON:
                        raise TungstenSwitchedOff

                elif calib.template.id == TemplateID.SKY_FLAT:
                    if np.isnan(calib.exposure_time):
                        # Compute exposure time
                        if prev_exptime is None or img is None:
                            calib.exposure_time = exposure.flat_exptime(
                                config.Calib.Flats.target_adu, calib.filter)
                        else:
                            calib.exposure_time = exposure.next_flat_exptime(
                                config.Calib.Flats.target_adu, img,
                                prev_exptime, prev_filter, calib.filter)

                        memory.hset('calibration_poses', 'list',
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

                seq_utils.set_sequencer_status(SequencerStatus.EXPOSING,
                                               check_abort=True)

                logger.info(
                    'sequencer',
                    f'Taking image for {calib.template.id.name}, exposure time = {calib.exposure_time:.3f} s'
                )

                calib.status = 'EXPOSING'
                memory.hset('calibration_poses', 'list',
                            encoder.encode(calib_list))

                image_path = camera.take_science_image(
                    calib.template, exptime=calib.exposure_time)

                if image_path is None:
                    raise CameraTakeImageFailed

                prev_exptime = calib.exposure_time
                img = fits.getdata(image_path)

                calib.median = np.median(img)
                calib.status = 'OK'
                memory.hset('calibration_poses', 'list',
                            encoder.encode(calib_list))

                # Check if an abort was requested
                if seq_utils.is_aborting():
                    raise AbortRequested

            except AbortRequested as exc:
                calib.status = 'ERROR'
                memory.hset('calibration_poses', 'list',
                            encoder.encode(calib_list))

                raise exc

            except (SkyFlatExptimeTooHigh, SkyFlatExptimeTooLow) as exc:
                calib.status = 'SKIPPED'
                calib.error_text = exc.__doc__
                memory.hset('calibration_poses', 'list',
                            encoder.encode(calib_list))

                continue

            except SequencerException as exc:
                logger.error(
                    'sequencer',
                    f'"{exc.__doc__}" happened during calibration pose')

                calib.status = 'ERROR'
                calib.error_text = exc.__doc__
                memory.hset('calibration_poses', 'list',
                            encoder.encode(calib_list))

                continue

        # Note: do not turn off tungsten in case of successive flats

        if shutter.close() != ShutterStatus.CLOSED:
            logger.error(
                'sequencer',
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
