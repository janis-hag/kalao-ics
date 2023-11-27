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

from kalao import system
from kalao.cacao import aocontrol
from kalao.fli import camera
from kalao.plc import (adc, calib_unit, core, filterwheel, flip_mirror, laser,
                       shutter, tungsten)
from kalao.utils import database, file_handling, starfinder

from tcs_communication import t120

from kalao.definitions.enums import (FlipMirrorPosition, LoopStatus,
                                     ReturnCode, SequencerStatus, ShutterState,
                                     TrackingStatus, TungstenStatus)
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

    database.store('obs', {'tracking_status': TrackingStatus.IDLE})

    if None in (q, dit, nbPic):
        raise MissingKeyword

    if core.lamps_off() != 0:
        raise LampsNotOff

    if shutter.close() != ShutterState.CLOSED:
        raise ShutterNotClosed

    # Check if an abort was requested before taking image
    _check_abort(q)

    filepath = file_handling.generate_image_filepath()

    # Take nbPic image
    for _ in range(nbPic):
        #seq_command_received = database.get_latest_record_value('obs', 'sequencer_command_received')
        image_path = camera.take_image(dit=dit, filepath=filepath,
                                       sequencer_arguments=seq_args)

        if image_path is None:
            raise FLITakeImageFailed

        # Check if an abort was requested
        _check_abort(q)

    return ReturnCode.SEQ_OK


def dark_abort(**seq_args):
    """
    Send abort instruction to fli camera and change sequencer status to 'WAITING'.
    :return: nothing
    """

    return _abort_camera()


def tungsten_FLAT(**seq_args):
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

    database.store('obs', {'tracking_status': TrackingStatus.IDLE})

    # Commented out as it is not clear what is meant to be checked
    # if None in (q):
    #     return ReturnCode.MissingKeyword

    if aocontrol.emgain_off() == -1:
        raise EMGainNotOff

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if tungsten.on() != 'ON':
        raise TungstenNotOn

    if calib_unit.move_to_tungsten_position() == -1:
        raise TungstenNotInPosition

    if shutter.close() != ShutterState.CLOSED:
        raise ShutterNotClosed

    if flip_mirror.up() != FlipMirrorPosition.UP:
        raise FlipMirrorNotUp

    if filterwheel.set_filter(filter_list[0]) != filter_list[0]:
        raise FilterWheelNotInPosition

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
        if tungsten.plc_status()['nStatus'] != 2:
            raise TungstenSwitchedOff

        if filterwheel.set_filter(filter_name) != filter_name:
            raise FilterWheelNotInPosition

        dit = config.Tungsten.flat_dit_list[filter_name]

        image_path = file_handling.generate_image_filepath()

        image_path = camera.take_image(dit=dit, filepath=image_path,
                                       sequencer_arguments=seq_args)

        if image_path is None:
            raise FLITakeImageFailed

        # block for each picture and check if an abort was requested
        _check_abort(q)

    # TODO move tungsen.off() to start of other commands so that the lamp stays on if needed
    # tungsten.off()
    return ReturnCode.SEQ_OK


def tungsten_FLAT_abort(**seq_args):
    """
    Send abort instruction to fli camera and change sequencer status to 'WAITING'.
    :return: nothing
    """

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

    database.store('obs', {'tracking_status': TrackingStatus.POINTING})

    #if None in (q, dit, filepath):
    if q is None:
        # TODO verify which arguments are actually needed.
        raise MissingKeyword

    if aocontrol.emgain_off() == -1:
        raise EMGainNotOff

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if core.lamps_off() != 0:
        raise LampsNotOff

    if flip_mirror.down() != FlipMirrorPosition.DOWN:
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

    ref_dit = starfinder.optimise_dit(5, sequencer_arguments=seq_args,
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

        #dit = starfinder.optimise_dit(5, sequencer_arguments=seq_args)

        image_path = camera.take_image(dit=dit_list[filter_name],
                                       sequencer_arguments=seq_args)

        if image_path is None:
            raise FLITakeImageFailed

        # Check if an abort was requested
        _check_abort(q)

    if shutter.close() != ShutterState.CLOSED:
        system.print_and_log('[ERROR] Failed to close the shutter')  #TODO

    return ReturnCode.SEQ_OK


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
    centering = seq_args.get('centering')
    mag_v = seq_args.get('mv')

    if kalfilter is None:
        system.print_and_log(
            '[WARNING] No filter specified for take_image, using clear')
        kalfilter = 'clear'

    if centering == 'aut' or not database.get_last_value(
            'obs', 'tracking_status') == TrackingStatus.TRACKING:

        database.store('obs', {'tracking_status': TrackingStatus.POINTING})
        aocontrol.open_loops()
        aocontrol.reset_all_dms()

    if None in (q, dit):
        raise MissingKeyword

    fo_delta = starfinder.get_latest_fo_delta()
    if fo_delta is not None:
        system.print_and_log("Updating autofocus")
        t120.update_fo_delta(fo_delta)
        t120.request_autofocus()

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if core.lamps_off() != 0:
        raise LampsNotOff

    if flip_mirror.down() != FlipMirrorPosition.DOWN:
        raise FlipMirrorNotDown

    if shutter.open() != ShutterState.OPEN:
        raise ShutterNotOpen

    # Put filter on clear to center on target
    if centering == 'aut' and filterwheel.set_filter('clear') != 'clear':
        raise FilterWheelNotInPosition

    _wait_for_tracking()

    # Configure ADC once on target (otherwise RA/DEC coordinates are not up-to-date)
    if adc.configure() != 0:
        raise ADCConfigureFailed

    if kao == 'NO_AO':
        if aocontrol.open_loops() != LoopStatus.ALL_LOOPS_OFF:
            raise LoopsNotOpen

    if centering == 'aut' or kao == 'AO':
        acq_dit = config.FLI.exp_time
        if 8 < float(mag_v) < 10:
            acq_dit = 10
        if 10 < float(mag_v):
            acq_dit = 20

        _center_on_target(kao=kao, dit=acq_dit)

    # Move filter to correct position for science
    if filterwheel.set_filter(kalfilter) != kalfilter:
        raise FilterWheelNotInPosition

    if kao == 'AO':
        system.print_and_log("Trying to close loop")

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

        system.print_and_log("Initial tip/tilt offload to telescope")

        aocontrol.tip_tilt_offload_ttm_to_telescope(override_threshold=True)

        time.sleep(config.Starfinder.AO_wait_settle)

    image_path = file_handling.generate_image_filepath()

    image_path = camera.take_image(dit=dit, filepath=image_path,
                                   sequencer_arguments=seq_args)

    #Monitor AO and cancel exposure if needed

    if image_path is None:
        raise FLITakeImageFailed

    return ReturnCode.SEQ_OK


def target_observation_abort(**seq_args):
    """
    Send abort instruction to fli camera and change sequencer status to 'WAITING'.

    :return: nothing
    """

    return _abort_camera()


def focusing(**seq_args):
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
        #system.print_and_log("[WARNING] No filter specified for take image, using clear")
        kalfilter = 'clear'

    database.store('obs', {'tracking_status': TrackingStatus.POINTING})

    if q is None:
        raise MissingKeyword

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if aocontrol.reset_all_dms() != 0:
        raise DMResetFailed

    if core.lamps_off() != 0:
        raise LampsNotOff

    if flip_mirror.down() != FlipMirrorPosition.DOWN:
        raise FlipMirrorNotDown

    if shutter.open() != ShutterState.OPEN:
        raise ShutterNotOpen

    _wait_for_tracking()

    # Configure ADC once on target (otherwise RA/DEC coordinates are not up-to-date)
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

    ret = starfinder.focus_sequence(focus_points=6, focusing_dit=dit,
                                    sequencer_arguments=seq_args)

    if ret != 0:
        raise FLITakeImageFailed

    return ReturnCode.SEQ_OK


def focusing_abort(**seq_args):
    """
    Send abort instruction to fli camera and change sequencer status to 'WAITING'.
    :return: nothing
    """

    # TODO also send abort to focus_sequence not only to camera

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

    if core.lamps_off() != 0:
        raise LampsNotOff

    return ReturnCode.SEQ_OK


def abort(**seq_args):
    """
    Send abort instruction to fli camera and change sequencer status to 'WAITING'.
    :return: nothing
    """

    return _abort_camera()


def instrument_change(**seq_args):
    """
    Change of instrument operation, go into standby mode.

    :return: nothing
    """

    aocontrol.open_loops()
    aocontrol.emgain_off()
    aocontrol.set_exptime(0)

    # Note: do not turn DM off (only at the end of the night)

    ret = tungsten.off()
    if (ret != 0):
        # TODO handle error
        system.print_and_log(ret)

    ret = laser.disable()
    if ret != 0:
        # TODO handle error
        system.print_and_log(ret)

    ret = shutter.close()
    if ret != 0:
        # TODO handle error
        system.print_and_log(ret)

    database.store('obs', {
        'tracking_manual_centering': False,
        'tracking_status': TrackingStatus.IDLE
    })

    # request_manual_centering(False)
    # change tracking flaf

    system.print_and_log('INSTRUMENTCHANGE received moving into standby.')

    return ReturnCode.SEQ_OK


def stopao(**seq_args):
    """
    Change of target. Stopping AO

    :return: nothing
    """

    aocontrol.open_loops()
    aocontrol.emgain_off()
    aocontrol.set_exptime(0)

    database.store('obs', {
        'tracking_manual_centering': False,
        'tracking_status': TrackingStatus.IDLE
    })

    # request_manual_centering(False)
    # change tracking flaf

    system.print_and_log('STOPAO received, opening loop.')

    return ReturnCode.SEQ_OK


def end(**seq_args):
    """
    End of instrument operation, go into standby mode and starting morning calibrations.

    :return: nothing
    """

    aocontrol.open_loops()
    aocontrol.emgain_off()
    aocontrol.set_exptime(0)

    database.store('obs', {'tracking_status': TrackingStatus.IDLE})

    ret = tungsten.off()
    if (ret != 0):
        # TODO handle error
        system.print_and_log(ret)

    ret = laser.disable()
    if ret != 0:
        # TODO handle error
        system.print_and_log(ret)

    ret = shutter.close()
    if ret != 0:
        # TODO handle error
        system.print_and_log(ret)

    ret = aocontrol.turn_dm_off()
    if ret != 0:
        system.print_and_log('[ERROR] Unable to turn off DM')

    # Set to waiting for the Euler synchro to be released
    database.store(
        'obs', {
            'sequencer_status': SequencerStatus.WAITING,
            'tracking_manual_centering': False
        })

    time.sleep(2)

    database.store('obs', {'sequencer_status': SequencerStatus.BUSY})
    # Generate darks for this night
    starfinder.generate_night_darks()

    # request_manual_centering(False)
    # change tracking flag

    system.print_and_log('END received moving into standby.')

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
        message = q.get()

        if message == 'abort':
            raise AbortRequested
        else:
            q.put(message)

    return ReturnCode.SEQ_OK


def _abort_camera():
    ret = camera.cancel()
    if ret != 0:
        raise FLICancelFailed

    time.sleep(1)

    # two cancel are done to avoid concurrency problems
    ret = camera.cancel()
    if ret != 0:
        raise FLICancelFailed

    return ReturnCode.SEQ_OK


def _wait_for_tracking():
    """
    Waits for the telescope to be on target

    :return: 0 or 1 depending on success pointing
    """
    t0 = time.monotonic()

    while time.monotonic() - t0 < config.SEQ.pointing_timeout:
        tracking_status = database.get_last_value('obs', 'tracking_status')

        if tracking_status == TrackingStatus.TRACKING:
            file_handling.update_db_from_telheader()
            return ReturnCode.SEQ_OK

        time.sleep(config.SEQ.pointing_wait_time)

    else:
        system.print_and_log('[ERROR] Timeout while waiting to be on target.')

        raise TrackingTimeout


def _center_on_target(kao, dit):
    previous_tracking_status = database.get_last('obs',
                                                 'tracking_status')  # TODO
    database.store('obs', {'tracking_status': TrackingStatus.CENTERING})

    ret = starfinder.center_on_target(kao=kao, dit=dit)

    if ret != ReturnCode.CENTERING_OK:
        raise CenteringFailed

    database.store('obs', {'tracking_status': TrackingStatus.TRACKING})

    return ret


def _wait_for_tungsten(q):
    # Wait for tungsten to warm up
    state, switch_time = tungsten.get_switch_time()

    database.store('obs', {'sequencer_status': SequencerStatus.WAITLAMP})

    while switch_time < config.Tungsten.stabilisation_time:
        # Check if lamp is still on
        if state != TungstenStatus.ON:
            raise TungstenSwitchedOff

        _check_abort(q)

        time.sleep(config.Tungsten.switch_wait)

        state, switch_time = tungsten.get_switch_time()

    database.store('obs', {'sequencer_status': SequencerStatus.BUSY})

    return ReturnCode.SEQ_OK


commands = {
    "K_DARK": dark,
    "K_DARK_ABORT": dark_abort,
    "K_LMPFLT": tungsten_FLAT,
    "K_LMPFLT_ABORT": tungsten_FLAT_abort,
    "K_SKYFLT": sky_flat,
    "K_TRGOBS": target_observation,
    "K_TRGOBS_ABORT": target_observation_abort,
    "K_LAMPON": lamp_on,
    "K_LAMPOF": lamp_off,
    "K_FOCUS": focusing,
    "K_FOCUS_ABORT": focusing_abort,
    "K_CONFIG": edp_config,
    "ABORT": abort,
    "INSTRUMENTCHANGE": instrument_change,
    "THE_END": end,
    "K_ENDCAL": end,
    "STOPAO": stopao,
}
