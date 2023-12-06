import time

import numpy as np
import pandas as pd

from astropy.io import fits

from kalao import system
from kalao.cacao import aocontrol
from kalao.fli import camera
from kalao.plc import calib_unit, filterwheel, flip_mirror, laser, shutter
from kalao.utils import database, file_handling, kalao_time
from kalao.utils.starfinder import find_star_custom_algo, find_star_fits

from tcs_communication import t120

from kalao.definitions.enums import (FlipMirrorPosition, ReturnCode,
                                     SequencerStatus, ShutterState)
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
    #             tt_threshold=config.AO.WFS_centering_slope_threshold)
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
            system.print_and_log(f'ERROR no image received.')
            return -1

        x, y, peak, fwhm = find_star_fits(image_path)

        if x != -1 and y != -1:

            send_pixel_offset(x, y)

            image_path = camera.take_image(dit=dit)
            if image_path is None:
                system.print_and_log(f'ERROR no image received.')
                return -1

            x, y, peak, fwhm = find_star_fits(image_path)

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
                    system.print_and_log(
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
    if np.abs(calib_unit.get_position() - config.Laser.position) > 0.5:
        calib_unit.move_to_laser_position()

    if filterwheel.set_filter(
            config.FLI.laser_calib_filter) != config.FLI.laser_calib_filter:
        raise FilterWheelNotInPosition

    if shutter.close() != ShutterState.CLOSED:
        raise ShutterNotClosed

    if flip_mirror.up() != FlipMirrorPosition.UP:
        raise FlipMirrorNotUp

    laser.set_intensity(config.FLI.laser_calib_intensity)

    # Reset tip tilt stream to 0
    aocontrol.reset_dm(config.AO.TTM_loop_number)

    # Rough centering loop with FLI
    for i in range(3):
        print(f'Centering step {i}')

        image = camera.take_frame(dit=config.FLI.laser_calib_dit)

        # X can be changed by the ttm_tip_offset value
        # Y can be changed by the calib_unit position or ttm_tilt_offset value
        x, y = find_star_custom_algo(image, spot_size=7, estim_error=0.05,
                                     nb_step=5, laser_spot=True)

        if x != -1 and y != -1:
            calib_unit.move_px(config.FLI.center_y - y)
            time.sleep(3)

        # Check the new x position after the calib unit has been moved
        image = camera.take_frame(dit=config.FLI.laser_calib_dit)

        # X can be changed by the ttm_tip_offset value
        # Y can be changed by the calib_unit position or ttm_tilt_offset value
        x, y = find_star_custom_algo(image, spot_size=7, estim_error=0.05,
                                     nb_step=5, laser_spot=True)

        if x != -1 and y != -1:
            aocontrol.tip_tilt_offset_fli_to_ttm(x - config.FLI.center_x, 0)

    # Precise centering with WFS
    aocontrol.emgain_off()

    laser.set_intensity(config.WFS.laser_calib_intensity)
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


def focus_sequence(focus_points=4, focusing_dit=config.Starfinder.focusing_dit,
                   sequencer_arguments=None):
    """
    Starts a sequence to find best telescope M2 focus position.

    TODO normalise flux by integration time and adapt focusing_dit in case of saturation
    TODO handle abort of sequence

    :param sequencer_arguments:
    :param focus_points: number of points to take for in the sequence
    :param focusing_dit: integration time for each image
    :return:
    """

    if sequencer_arguments is None:
        q = None
    else:
        q = sequencer_arguments.get('q')

    # TODO define focusing_dit in kalao.config or pass as argument
    focus_points = np.around(focus_points)

    initial_focus = t120.get_focus_value()

    # focusing_dit = optimise_dit(focusing_dit)
    #
    # if focusing_dit == -1:
    #     system.print_and_log(
    #             'Error optimising dit for focusing sequence. Target brightness out of range'
    #     )

    file_path = camera.take_image(dit=focusing_dit,
                                  sequencer_arguments=sequencer_arguments)

    #time.sleep(5)
    file_handling.add_comment(file_path, 'Focus sequence: 0')

    image = fits.getdata(file_path)
    flux = np.sort(np.ravel(image))[-config.Starfinder.focusing_pixels:].sum()

    if flux < config.Starfinder.min_flux:
        database.store(
            'obs', {
                'sequencer_log': '[ERROR] No flux detected',
                'sequencer_status': SequencerStatus.ERROR
            })
        return -1

    focus_flux = pd.DataFrame({'set_focus': [initial_focus], 'flux': [flux]})

    # Get even number of focus_points in order to include 0 in the sequence.
    if (focus_points % 2) == 1:
        focus_points = focus_points + 1

    focusing_sequence = (np.arange(focus_points + 1) -
                         focus_points/2) * config.Starfinder.focusing_step

    for step, focus_offset in enumerate(focusing_sequence):
        database.store(
            'obs',
            {
                'sequencer_log': f'Focus {step+1}:{len(focusing_sequence)}',
                'sequencer_status':
                    f'Focus {step+1}:{len(focusing_sequence)}'  #TODO: this is irregular, do better
            })

        # Check if an abort was requested
        if q is not None and not q.empty():
            q.get()
            return -1
        if focus_offset == 0:
            # skip set_focus zero as it was already taken
            continue

        new_focus = focus_offset + initial_focus

        t120.send_focus_offset(new_focus)

        # TODO: Remove sleep if send_focus is blocking
        time.sleep(15)

        file_path = camera.take_image(dit=focusing_dit,
                                      sequencer_arguments=sequencer_arguments)

        file_handling.add_comment(file_path, f'Focus sequence: {new_focus}')

        image = fits.getdata(file_path)

        flux = np.sort(
            np.ravel(image))[-config.Starfinder.focusing_pixels:].sum()

        focus_flux.loc[len(focus_flux.index)] = [new_focus, flux]

    # Keep best set_focus
    best_focus = focus_flux.loc[focus_flux['flux'].idxmax(), 'set_focus']

    print(focus_flux)

    database.store('obs', {'sequencer_log': f'Best focus value: {best_focus}'})

    temps = t120.get_tube_temp()

    if (time.time() -
            float(temps.tunix)) < float(config.T120.temperature_file_timeout):

        database.store(
            'obs', {
                'focusing_best': best_focus,
                'focusing_temttb': temps.temttb,
                'focusing_temtth': temps.temtth,
                'focusing_fo_delta': best_focus - initial_focus
            })

    # best_focus = initial_focus + correction
    t120.update_fo_delta(best_focus - initial_focus)

    return 0


def get_latest_fo_delta():

    fo_delta_record = database.get_last('obs', 'focusing_fo_delta')

    if fo_delta_record == {}:
        return None

    fo_delta_age = (kalao_time.now() -
                    fo_delta_record['timestamp']).total_seconds()

    if fo_delta_age > 12 * 3600:
        return None
    else:
        return fo_delta_record['value']


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
        system.print_and_log(
            f'WARN: Not generating darks as {science_folder} is empty.')
        return 0
    else:
        for dit in exp_times:
            for i in range(10):
                print(dit, i)
                image_path = camera.take_dark(dit=dit)
                with fits.open(image_path, mode='update') as hdul:
                    hdul[0].header.set('HIERARCH ESO TPL ID', 'K_DARK')
                    hdul[0].header.set('HIERARCH ESO OBS TARGET NAME', 'Dark')
                    hdul.flush()

    return 0
