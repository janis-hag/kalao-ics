import time

import numpy as np

from kalao import database, logger
from kalao.cacao import aocontrol
from kalao.fli import camera
from kalao.interfaces import etcs
from kalao.plc import calibunit, filterwheel, flipmirror, laser, shutter
from kalao.sequencer.seq_context import with_sequencer_status
from kalao.utils import starfinder

from kalao.definitions.enums import (FlipMirrorPosition, ObservationType,
                                     ReturnCode, SequencerStatus, ShutterState)
from kalao.definitions.exceptions import (DMNotOn, FilterWheelNotInPosition,
                                          FlipMirrorNotUp,
                                          ManualCenteringTimeout,
                                          ShutterNotClosed, WFSNotOn)

import config


@with_sequencer_status(SequencerStatus.CENTERING)
def center_on_target(kao='NO_AO', dit=config.FLI.exp_time):
    """
    Start star centering sequence:
    - Sets this filter based on filter_arg request.
    - Takes an image and search for the star position.
    - Send telescope offsets based on the measured position.
    - If auto centering does not work request manual centering

    :param dit:
    :param kao: flag to indicate if AO will be used, set to no by default.

    :return: 0 if centering succeded
    """

    timeout_time = time.monotonic(
    ) + config.Starfinder.centering_timeout + 3*dit

    # Check if we are alread on the star
    # if check_wfs_flux() == 0:
    #     # Start WFS centering procedure
    #     aocontrol.wfs_centering(
    #             tt_threshold=config.WFS.centering_slope_threshold)
    #
    #     request_manual_centering(False)
    #
    #     return 0

    # Reset tip tilt stream to 0
    #aocontrol.reset_dm(config.AO.TTM_loop_number)

    while time.monotonic() < timeout_time:

        # Check if we are already on target
        if kao == 'AO':
            # Check if enough light is on the WFS for precise centering
            if aocontrol.optimize_wfs_flux() == 0:
                # if aocontrol.check_loops() != LoopStatus.ALL_LOOPS_ON:
                #     # Start WFS centering procedure
                #     aocontrol.wfs_centering(tt_threshold=config.AO.
                #                             WFS_centering_slope_threshold)
                #     aocontrol.tiptilt_offload_ttm_to_telescope()

                return ReturnCode.CENTERING_OK

        # TODO use exptime given by nseq args
        image_path = camera.take_image(ObservationType.CENTERING, dit=dit)

        # TODO add dit optimisation
        #  focusing_dit = optimise_dit(focusing_dit)

        if image_path is None:
            logger.error('centering', 'No image received.')
            return -1

        x, y, peak, fwhm = starfinder.find_star_fits(image_path)

        if x != -1 and y != -1:

            tiptilt_fli_to_telescope(x - config.FLI.center_x,
                                     y - config.FLI.center_y)

            image_path = camera.take_image(ObservationType.CENTERING, dit=dit)
            if image_path is None:
                logger.error('centering', 'No image received.')
                return -1

            x, y, peak, fwhm = starfinder.find_star_fits(image_path)

            if x != -1 and y != -1:
                # Fine centering with TTM
                aocontrol.tiptilt_fli_to_ttm(x - config.FLI.center_x,
                                             y - config.FLI.center_y)

            if kao == 'AO':
                # Check if enough light is on the WFS for precise centering
                if aocontrol.optimize_wfs_flux() == 0:
                    # Start WFS centering procedure
                    #aocontrol.wfs_centering(tt_threshold=config.AO.
                    #                        WFS_centering_slope_threshold)

                    return ReturnCode.CENTERING_OK
                else:
                    # Retry centering
                    logger.error('centering',
                                 'No light on WFS, re-centering with FLI')
                    continue

            else:
                # Centering is good enough
                return ReturnCode.CENTERING_OK

        else:
            # Start manual centering
            # TODO start timeout (value in kalao.config)
            # Set flag for manual centering
            request_manual_centering()

            # Wait 10 seconds before trying another star detection
            time.sleep(10)
            continue

            # if kao == 'AO':
            #     while time.monotonic() < timeout_time:
            #
            #         # Check if we are centered and exit loop
            #         ret = optimize_wfs_flux()
            #         if ret == 0:
            #             request_manual_centering(False)
            #             return 0

            #
            # else:
            #     # TODO for centering
            #     return 0

            # TODO wait for observer input
            # TODO send gop message
            # TODO send offset to telescope
            # TODO verify if SHWFS enough illuminated
            # if shwfs ok:
            #    return 0

    else:
        return ReturnCode.CENTERING_TIMEOUT


@with_sequencer_status(SequencerStatus.CENTERING)
def center_on_laser():
    """
    Center the calibration unit the laser on the WFS.

    1. Move calibration unit close to correct position
    1. Close shutter
    2. Turn laser on
    3. Move flip mirror up
    4. Get laser offset
    5. Move calibration unit to new position

    :return:
    """

    if aocontrol.turn_dm_on() != 0:
        raise DMNotOn

    if aocontrol.start_wfs_acquisition() != 0:
        raise WFSNotOn

    # Move calib unit to approximately correct position if too far #TODO: make similar to others
    if np.abs(calibunit.get_position() - config.Laser.position) > 0.5:
        calibunit.move_to_laser_position()

    if filterwheel.set_filter(
            config.FLI.laser_calib_filter) != config.FLI.laser_calib_filter:
        raise FilterWheelNotInPosition

    if shutter.close() != ShutterState.CLOSED:
        raise ShutterNotClosed

    if flipmirror.up() != FlipMirrorPosition.UP:
        raise FlipMirrorNotUp

    laser.set_power(config.FLI.laser_calib_power, enable=True)

    # Reset tip tilt stream to 0
    aocontrol.reset_dm(config.AO.TTM_loop_number)

    # Rough centering loop with FLI
    for i in range(3):
        print(f'Centering step {i}')

        image = camera.take_frame(dit=config.FLI.laser_calib_dit)

        # X can be changed by the ttm_tip_offset value
        # Y can be changed by the calibunit position or ttm_tilt_offset value
        x, y = starfinder.find_star_custom_algo(image, spot_size=7,
                                                estim_error=0.05, nb_step=5,
                                                laser_spot=True)

        if x != -1 and y != -1:
            calibunit.move_px(config.FLI.center_y - y)
            time.sleep(3)

        # Check the new x position after the calib unit has been moved
        image = camera.take_frame(dit=config.FLI.laser_calib_dit)

        # X can be changed by the ttm_tip_offset value
        # Y can be changed by the calibunit position or ttm_tilt_offset value
        x, y = starfinder.find_star_custom_algo(image, spot_size=7,
                                                estim_error=0.05, nb_step=5,
                                                laser_spot=True)

        if x != -1 and y != -1:
            aocontrol.tiptilt_fli_to_ttm(x - config.FLI.center_x, 0)

    # Precise centering with WFS
    aocontrol.emgain_off()

    laser.set_power(config.WFS.laser_calib_power, enable=True)
    aocontrol.set_exptime(config.WFS.laser_calib_exptime)

    aocontrol.tiptilt_wfs_to_ttm()

    return 0


def request_manual_centering():
    logger.info('centering', 'Starting manual centering.')
    database.store('obs', {'tracking_manual_centering': True})

    timeout = time.monotonic() + config.Centering.manual_timeout

    while time.monotonic() < timeout:
        centering = database.get_last_value('obs', 'tracking_manual_centering')

        if centering is False:
            return 0

        time.sleep(1)
    else:
        logger.error('centering',
                     'Timeout while waiting for manual centering from user.')
        raise ManualCenteringTimeout


def validate_manual_centering():
    logger.info('centering', 'Manual centering done.')
    database.store('obs', {'tracking_manual_centering': False})


def manual_centering(x, y, AO=False):
    # TODO add docstring
    # TODO verify value validity before sending

    tiptilt_fli_to_telescope(x - config.FLI.center_x, y - config.FLI.center_y)
    image_path = camera.take_image(ObservationType.CENTERING,
                                   dit=config.FLI.exp_time)
    if image_path is None:
        ret = -1
    else:
        ret = 0

    if AO:
        ret = aocontrol.optimize_wfs_flux()

    return ret


def tiptilt_fli_to_telescope(x, y, gain=1):
    """
    Send offsets to telescope converting the pixel offset into telescope alt/az offset.

    :param x: pixel offset along the x axis
    :param y: pixel offset along the y axis
    :return: success status
    """

    alt_offset = x * config.FLI.tip_to_onsky * gain
    az_offset = y * config.FLI.tilt_to_onsky * gain

    etcs.send_altaz_offset(alt_offset, az_offset)

    return 0
