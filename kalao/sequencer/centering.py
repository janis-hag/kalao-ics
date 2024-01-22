import time

import numpy as np

from astropy.io import fits

from kalao import database, logger
from kalao.cacao import aocontrol, toolbox
from kalao.fli import camera
from kalao.plc import calibunit, filterwheel, flipmirror, laser, shutter
from kalao.sequencer.seq_context import with_sequencer_status
from kalao.utils import offsets, starfinder

from kalao.definitions.enums import (AdaptiveOpticsMode, CenteringMode,
                                     FlipMirrorPosition, ObservationType,
                                     ReturnCode, SequencerStatus, ShutterState)
from kalao.definitions.exceptions import (
    AbortRequested, AutomaticCenteringTimeout, CenteringException,
    CenteringFluxWFSTooLow, CenteringMaxIter, CenteringStarNotFound, DMNotOn,
    FilterWheelNotInPosition, FlipMirrorNotUp, FLITakeImageFailed,
    ManualCenteringTimeout, ShutterNotClosed, WFSNotOn)

import config


@with_sequencer_status(SequencerStatus.CENTERING)
def center_on_target(dit, centering_mode=CenteringMode.AUTOMATIC,
                     adaptiveoptics_mode=AdaptiveOpticsMode.DISABLED):
    """
    Start star centering sequence:
    - Sets this filter based on filter_arg request.
    - Takes an image and search for the star position.
    - Send telescope offsets based on the measured position.
    - If auto centering does not work request manual centering

    :param dit:
    :param adaptiveoptics_mode: flag to indicate if AO will be used, set to no by default.

    :return: 0 if centering succeded
    """

    if centering_mode == CenteringMode.NONE:
        return

    timeout = time.monotonic() + config.Centering.automatic_timeout

    if centering_mode == CenteringMode.AUTOMATIC:
        logger.info('centering', f'Starting automatic centering')

        try:
            xy = _get_star(dit)
            on_fli_with_telescope(dit=dit, xy=xy, timeout=timeout)
            on_fli_with_ttm(dit=dit, xy=xy, timeout=timeout)
        except (AbortRequested, FLITakeImageFailed) as e:
            logger.error('centering',
                         f'"{e.__doc__}" happened during centering on target')

            raise e
        except CenteringException as e:
            logger.error(
                'centering',
                f'"{e.__doc__}" happened during centering on target, switching to manual'
            )

            # Will wait until manual centering is done, or raise an exception if manual centering timeout is reached
            request_manual_centering()
    else:
        logger.info('centering', f'Starting manual centering')

        # Take at least one image so the observer can click on it
        img_path = camera.take_image(ObservationType.CENTERING)

        if img_path is None:
            raise FLITakeImageFailed

        # Will wait until manual centering is done, or raise an exception if manual centering timeout is reached
        request_manual_centering()

    if adaptiveoptics_mode == AdaptiveOpticsMode.ENABLED:
        # Check if enough light is on the WFS for precise centering
        if aocontrol.optimize_wfs_flux() != 0:
            raise CenteringFluxWFSTooLow

        try:
            on_wfs_with_ttm()
        except (CenteringException, AbortRequested, FLITakeImageFailed) as e:
            logger.error('centering',
                         f'"{e.__doc__}" happened during centering on target')

            raise e

    logger.info('centering', f'Centering done')

    return ReturnCode.CENTERING_OK


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

    logger.info('centering', f'Starting centering on laser')

    try:
        xy = _get_star(config.FLI.laser_calib_dit)
        on_fli_with_calibunit(dit=config.FLI.laser_calib_dit, xy=xy)
        on_fli_with_ttm(dit=config.FLI.laser_calib_dit, xy=xy)
    except (CenteringException, AbortRequested, FLITakeImageFailed) as e:
        logger.error('centering',
                     f'"{e.__doc__}" happened during centering on laser')
        return -1

    # Precise centering with WFS
    aocontrol.emgain_off()

    laser.set_power(config.WFS.laser_calib_power, enable=True)
    aocontrol.set_exptime(config.WFS.laser_calib_exptime)

    try:
        on_wfs_with_ttm()
    except (CenteringException, AbortRequested, FLITakeImageFailed) as e:
        logger.error('centering',
                     f'"{e.__doc__}" happened during centering on laser')
        return -1

    return ReturnCode.CENTERING_OK


def request_manual_centering():
    logger.info('centering', 'Starting manual centering.')
    database.store('obs', {'centering_manual': True})

    timeout = time.monotonic() + config.Centering.manual_timeout

    while time.monotonic() < timeout:
        centering = database.get_last_value('obs', 'centering_manual')

        if centering is False:
            return ReturnCode.CENTERING_OK

        if database.get_last_value(
                'sequencer_status') == SequencerStatus.ABORTING:
            database.store('obs', {'centering_manual': False})
            raise AbortRequested

        time.sleep(1)
    else:
        logger.error('centering',
                     'Timeout while waiting for manual centering from user.')
        database.store('obs', {'centering_manual': False})
        raise ManualCenteringTimeout


def validate_manual_centering():
    logger.info('centering', 'Manual centering done.')
    database.store('obs', {'centering_manual': False})

    return ReturnCode.CENTERING_OK


def manual_centering(x, y):
    dx = config.FLI.center_x - x
    dy = config.FLI.center_y - y

    offsets.fli_to_telescope(dx, dy)
    img_path = camera.take_image(ObservationType.CENTERING)

    if img_path is None:
        raise FLITakeImageFailed

    return ReturnCode.CENTERING_OK


def on_fli_with_calibunit(
        dit, xy=None, max_iter=config.Centering.fli_with_calibunit_max_iter,
        timeout=np.inf):
    if xy is None:
        x, y = _get_star(dit)
    else:
        x, y = xy

    logger.info('centering', 'Centering on FLI using calibration unit')

    for i in range(max_iter):
        dy = config.FLI.center_y - y
        error = np.abs(dy)

        if error <= config.Centering.fli_with_calibunit_precision:
            break

        _check_abort()

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info('centering', f'Centering step {i+1}, error = {error} px')

        offsets.fli_to_calibunit(dy)

        x, y = _get_star(dit)
    else:
        raise CenteringMaxIter

    logger.info('centering',
                f'Centered on FLI using calibration unit, error = {error} px')
    return ReturnCode.CENTERING_OK


def on_fli_with_telescope(
        dit, xy=None, max_iter=config.Centering.fli_with_telescope_max_iter,
        timeout=np.inf):
    if xy is None:
        x, y = _get_star(dit)
    else:
        x, y = xy

    logger.info('centering', 'Centering on FLI using telescope')

    for i in range(max_iter):
        dx = config.FLI.center_x - x
        dy = config.FLI.center_y - y
        error = np.sqrt(dx**2 + dy**2)

        if error <= config.Centering.fli_with_telescope_precision:
            break

        _check_abort()

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info('centering', f'Centering step {i+1}, error = {error} px')

        offsets.fli_to_telescope(dx, dy)

        x, y = _get_star(dit)
    else:
        raise CenteringMaxIter

    logger.info('centering',
                f'Centered on FLI using telescope, error = {error} px')
    return ReturnCode.CENTERING_OK


def on_fli_with_ttm(dit, xy=None,
                    max_iter=config.Centering.fli_with_ttm_max_iter,
                    timeout=np.inf):
    if xy is None:
        x, y = _get_star(dit)
    else:
        x, y = xy

    logger.info('centering', 'Centering on FLI using Tip-Tilt Mirror')

    for i in range(max_iter):
        dx = config.FLI.center_x - x
        dy = config.FLI.center_y - y
        error = np.sqrt(dx**2 + dy**2)

        if error <= config.Centering.fli_with_ttm_precision:
            break

        _check_abort()

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info('centering', f'Centering step {i+1}, error = {error} px')

        offsets.fli_to_ttm(dx, dy)

        x, y = _get_star(dit)
    else:
        raise CenteringMaxIter

    logger.info('centering',
                f'Centered on FLI using Tip-Tilt Mirror, error = {error} px')
    return ReturnCode.CENTERING_OK


def on_wfs_with_ttm(max_iter=config.Centering.wfs_with_ttm_max_iter,
                    timeout=np.inf):
    logger.info('centering', 'Centering on WFS using Tip-Tilt Mirror')

    slopes_fps = toolbox.open_fps_once(config.FPS.SHWFS)

    if slopes_fps is None:
        logger.error('centering', f'{config.FPS.SHWFS} is missing')
        return -1

    for i in range(max_iter):
        dx = -slopes_fps.get_param('slope_x_avg')
        dy = -slopes_fps.get_param('slope_y_avg')
        error = np.sqrt(dx**2 + dy**2)

        if error <= config.Centering.wfs_with_ttm_precision:
            break

        _check_abort()

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info('centering', f'Centering step {i+1}, error = {error} px')

        offsets.wfs_to_ttm(dx, dy)
    else:
        raise CenteringMaxIter

    logger.info('centering',
                f'Centered on WFS using Tip-Tilt Mirror, error = {error} px')
    return ReturnCode.CENTERING_OK


def _check_abort():
    if database.get_last_value('obs',
                               'sequencer_status') == SequencerStatus.ABORTING:
        raise AbortRequested


def _get_star(dit):
    img_path = camera.take_image(ObservationType.CENTERING, dit=dit)

    if img_path is None:
        raise FLITakeImageFailed

    img = fits.getdata(img_path)

    x, y, peak, fwhm = starfinder.find_star(img)

    if np.isnan([x, y, peak, fwhm]).any():
        raise CenteringStarNotFound

    return x, y
