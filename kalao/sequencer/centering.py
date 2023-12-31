import time

import numpy as np

from astropy.io import fits

from kalao import database, logger
from kalao.cacao import aocontrol
from kalao.fli import camera
from kalao.plc import calibunit, filterwheel, flipmirror, laser, shutter
from kalao.utils import file_handling, starfinder

from tcs_communication import t120

from kalao.definitions.enums import (FlipMirrorPosition, ReturnCode,
                                     ShutterState)
from kalao.definitions.exceptions import (DMNotOn, FilterWheelNotInPosition,
                                          FlipMirrorNotUp, ShutterNotClosed)

import config


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
                #     aocontrol.tip_tilt_offload_ttm_to_telescope()

                return ReturnCode.CENTERING_OK

        # TODO use exptime given by nseq args
        image_path = camera.take_image(dit=dit)

        # TODO add dit optimisation
        #  focusing_dit = optimise_dit(focusing_dit)

        if image_path is None:
            logger.error('centering', 'No image received.')
            return -1

        x, y, peak, fwhm = starfinder.find_star_fits(image_path)

        if x != -1 and y != -1:

            send_pixel_offset(x, y)

            image_path = camera.take_image(dit=dit)
            if image_path is None:
                logger.error('centering', 'No image received.')
                return -1

            x, y, peak, fwhm = starfinder.find_star_fits(image_path)

            if x != -1 and y != -1:
                # Fine centering with TTM
                aocontrol.tip_tilt_offset_fli_to_ttm(x - config.FLI.center_x,
                                                     y - config.FLI.center_y)

            if kao == 'AO':
                # Check if enough light is on the WFS for precise centering
                if aocontrol.optimize_wfs_flux() == 0:
                    # Start WFS centering procedure
                    #aocontrol.wfs_centering(tt_threshold=config.AO.
                    #                        WFS_centering_slope_threshold)

                    request_manual_centering(False)

                    return ReturnCode.CENTERING_OK
                else:
                    # Retry centering
                    logger.error('centering',
                                 'No light on WFS, re-centering with FLI')
                    continue

            else:
                # Centering is good enough
                request_manual_centering(False)
                return ReturnCode.CENTERING_OK

        else:
            # Start manual centering
            # TODO start timeout (value in kalao.config)
            # Set flag for manual centering
            request_manual_centering(True)

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
            aocontrol.tip_tilt_offset_fli_to_ttm(x - config.FLI.center_x, 0)

    # Precise centering with WFS
    aocontrol.emgain_off()

    laser.set_power(config.WFS.laser_calib_power, enable=True)
    aocontrol.set_exptime(config.WFS.laser_calib_exptime)

    aocontrol.tip_tilt_wfs_to_ttm()

    return 0


def request_manual_centering(flag=True):
    # TODO add docstring

    database.store('obs', {'tracking_manual_centering': flag})


def manual_centering(x, y, AO=False, sequencer_arguments=None):
    # TODO add docstring
    # TODO verify value validity before sending

    send_pixel_offset(x, y)
    image_path = camera.take_image(dit=config.FLI.exp_time,
                                   sequencer_arguments=sequencer_arguments)
    if image_path is None:
        ret = -1
    else:
        ret = 0

    if AO:
        ret = aocontrol.optimize_wfs_flux()

    return ret


def send_pixel_offset(x, y):
    """
    Send offsets to telescope converting the pixel offset into telescope alt/az offset.

    :param x: pixel offset along the x axis
    :param y: pixel offset along the y axis
    :return: success status
    """

    alt_offset = (x - config.FLI.center_x) * config.FLI.px_x_to_onsky
    az_offset = (y - config.FLI.center_y) * config.FLI.px_y_to_onsky

    t120.send_altaz_offset(alt_offset, az_offset)

    time.sleep(2)

    return 0


def generate_night_darks(science_folder=None):
    """
    Generate the darks needed for the calibration of the night which is assumed to have ended.

    :param filepath:
    :return:
    """

    # TODO add docstring

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
                image_path = camera.take_dark(dit=dit)
                with fits.open(image_path, mode='update') as hdul:
                    hdul[0].header.set('HIERARCH ESO TPL ID', 'K_DARK')
                    hdul[0].header.set('HIERARCH ESO OBS TARGET NAME', 'Dark')
                    hdul.flush()

    return 0
