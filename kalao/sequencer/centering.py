import time

import numpy as np

from astropy.io import fits

from kalao import database, logger
from kalao.cacao import aocontrol, toolbox
from kalao.hardware import (calibunit, camera, dm, filterwheel, flipmirror,
                            laser, shutter, wfs)
from kalao.sequencer.seq_context import with_sequencer_status
from kalao.utils import offsets, starfinder

from kalao.definitions.enums import (AdaptiveOpticsMode, CenteringMode,
                                     FlipMirrorPosition, ObservationType,
                                     ReturnCode, SequencerStatus, ShutterState)
from kalao.definitions.exceptions import (
    AbortRequested, AutomaticCenteringTimeout, CameraTakeImageFailed,
    CenteringException, CenteringFluxWFSTooLow, CenteringMaxIter,
    CenteringOffsetingFailed, CenteringStarNotFound, DMNotOn,
    FilterWheelNotInPosition, FlipMirrorNotUp, ManualCenteringTimeout,
    ShutterNotClosed, WFSAcquisitionOff)

import config


@with_sequencer_status(SequencerStatus.CENTERING)
def center_on_target(
    exptime: float, centering_mode: CenteringMode = CenteringMode.AUTOMATIC,
    adaptiveoptics_mode: AdaptiveOpticsMode = AdaptiveOpticsMode.DISABLED
) -> ReturnCode:
    """
    Start star centering sequence:
    - Sets this filter based on filter_arg request.
    - Takes an image and search for the star position.
    - Send telescope offsets based on the measured position.
    - If auto centering does not work request manual centering

    :param exptime:
    :param adaptiveoptics_mode: flag to indicate if AO will be used, set to no by default.

    :return: 0 if centering succeded
    """

    if centering_mode == CenteringMode.NONE:
        return ReturnCode.CENTERING_OK

    timeout = time.monotonic() + config.Centering.automatic_timeout

    if centering_mode == CenteringMode.AUTOMATIC:
        logger.info('centering', 'Starting automatic centering')

        try:
            xy = _get_star(ObservationType.TARGET_CENTERING, exptime)
            xy = on_camera_with_telescope(ObservationType.TARGET_CENTERING,
                                          exptime=exptime, xy=xy,
                                          timeout=timeout)
            xy = on_camera_with_ttm(ObservationType.TARGET_CENTERING,
                                    exptime=exptime, xy=xy, timeout=timeout)
        except (AbortRequested, CameraTakeImageFailed) as e:
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
        logger.info('centering', 'Starting manual centering')

        # Take at least one image so the observer can click on it
        img_path = camera.take_image(ObservationType.TARGET_CENTERING)

        if img_path is None:
            raise CameraTakeImageFailed

        # Will wait until manual centering is done, or raise an exception if manual centering timeout is reached
        request_manual_centering()

    if adaptiveoptics_mode == AdaptiveOpticsMode.ENABLED:
        # Check if enough light is on the WFS for precise centering
        if aocontrol.optimize_wfs_flux() != ReturnCode.OK:
            raise CenteringFluxWFSTooLow

        # Note: currently disabled, let's let the AO do the centering by itself
        # try:
        #     on_wfs_with_ttm()
        # except (CenteringException, AbortRequested,
        #         CameraTakeImageFailed) as e:
        #     logger.error('centering',
        #                  f'"{e.__doc__}" happened during centering on target')
        #
        #     raise e

    logger.info('centering', 'Centering done')

    return ReturnCode.CENTERING_OK


@with_sequencer_status(SequencerStatus.CENTERING)
def center_on_laser() -> ReturnCode:
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

    logger.info('centering', 'Starting centering on laser')

    if dm.on() != ReturnCode.OK:
        raise DMNotOn

    if wfs.start_acquisition() != ReturnCode.OK:
        raise WFSAcquisitionOff

    if shutter.close() != ShutterState.CLOSED:
        raise ShutterNotClosed

    if flipmirror.up() != FlipMirrorPosition.UP:
        raise FlipMirrorNotUp

    if not aocontrol.check_wfs_flux():
        # Move calib unit to approximately correct position if too far
        if np.abs(calibunit.get_position() - config.Laser.position) > 0.5:
            calibunit.move_to_laser_position()

        if filterwheel.set_filter(config.Camera.laser_calib_filter
                                  ) != config.Camera.laser_calib_filter:
            raise FilterWheelNotInPosition

        laser.set_power(config.Camera.laser_calib_power, enable=True)

        # Reset tip tilt stream to 0
        aocontrol.reset_dm(config.AO.TTM_loop_number)

        try:
            xy = _get_star(ObservationType.LASER_CENTERING,
                           config.Camera.laser_calib_exptime)
            xy = on_camera_with_calibunit(
                ObservationType.LASER_CENTERING,
                exptime=config.Camera.laser_calib_exptime, xy=xy)
            xy = on_camera_with_ttm(ObservationType.LASER_CENTERING,
                                    exptime=config.Camera.laser_calib_exptime,
                                    xy=xy)
        except (CenteringException, AbortRequested,
                CameraTakeImageFailed) as e:
            logger.error('centering',
                         f'"{e.__doc__}" happened during centering on laser')
            return ReturnCode.CENTERING_ERROR

        # Precise centering with WFS
        aocontrol.emgain_off()

        laser.set_power(config.WFS.laser_calib_power, enable=True)
        aocontrol.set_exptime(config.WFS.laser_calib_exptime)
        aocontrol.set_emgain(config.WFS.laser_calib_emgain)

    try:
        on_wfs_with_ttm()
    except (CenteringException, AbortRequested, CameraTakeImageFailed) as e:
        logger.error('centering',
                     f'"{e.__doc__}" happened during centering on laser')
        return ReturnCode.CENTERING_ERROR

    return ReturnCode.CENTERING_OK


def request_manual_centering() -> ReturnCode:
    logger.info('centering', 'Starting manual centering.')
    database.store('obs', {'centering_manual': True})

    timeout = time.monotonic() + config.Centering.manual_timeout

    while time.monotonic() < timeout:
        centering = database.get_last_value('obs', 'centering_manual')

        if centering is False:
            break

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

    # If the user validated the centering before exposure ended, wait
    exposure_status = camera.get_exposure_status()
    while exposure_status['remaining_time'] > 0:
        time.sleep(1)

        _check_abort()

        exposure_status = camera.get_exposure_status()

    return ReturnCode.CENTERING_OK


def validate_manual_centering() -> ReturnCode:
    logger.info('centering', 'Manual centering done.')
    database.store('obs', {'centering_manual': False})

    return ReturnCode.CENTERING_OK


def manual_centering(dx: float, dy: float) -> ReturnCode:
    if offsets.camera_to_telescope(dx, dy) != ReturnCode.OK:
        raise CenteringOffsetingFailed

    img_path = camera.take_image(ObservationType.TARGET_CENTERING)

    if img_path is None:
        raise CameraTakeImageFailed

    return ReturnCode.CENTERING_OK


def on_camera_with_calibunit(obs_type: ObservationType, exptime: float,
                             xy: tuple[float, float] | None = None,
                             max_iter: int = config.Centering.
                             camera_with_calibunit_max_iter,
                             timeout: float = np.inf) -> tuple[float, float]:
    if xy is None:
        x, y = _get_star(obs_type, exptime)
    else:
        x, y = xy

    logger.info('centering', 'Centering on Camera using calibration unit')

    for i in range(max_iter):
        dy = config.Camera.center_y - y
        error = np.abs(dy)

        if error <= config.Centering.camera_with_calibunit_precision:
            break

        _check_abort()

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info('centering',
                    f'Centering step {i+1}, error = {error:.1f} px')

        offsets.camera_to_calibunit(dy)

        x, y = _get_star(obs_type, exptime)
    else:
        raise CenteringMaxIter

    logger.info(
        'centering',
        f'Centered on Camera using calibration unit, error = {error:.1f} px')
    return x, y


def on_camera_with_telescope(obs_type: ObservationType, exptime: float,
                             xy: tuple[float, float] | None = None,
                             max_iter: int = config.Centering.
                             camera_with_calibunit_max_iter,
                             timeout: float = np.inf) -> tuple[float, float]:
    if xy is None:
        x, y = _get_star(obs_type, exptime)
    else:
        x, y = xy

    logger.info('centering', 'Centering on Camera using telescope')

    for i in range(max_iter):
        dx = config.Camera.center_x - x
        dy = config.Camera.center_y - y
        error = np.sqrt(dx**2 + dy**2)

        if error <= config.Centering.camera_with_telescope_precision:
            break

        _check_abort()

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info('centering',
                    f'Centering step {i+1}, error = {error:.1f} px')

        if offsets.camera_to_telescope(dx, dy) != ReturnCode.OK:
            raise CenteringOffsetingFailed

        x, y = _get_star(obs_type, exptime)
    else:
        raise CenteringMaxIter

    logger.info('centering',
                f'Centered on Camera using telescope, error = {error:.1f} px')
    return x, y


def on_camera_with_ttm(obs_type: ObservationType, exptime: float,
                       xy: tuple[float, float] | None = None,
                       max_iter: int = config.Centering.
                       camera_with_calibunit_max_iter,
                       timeout: float = np.inf) -> tuple[float, float]:
    if xy is None:
        x, y = _get_star(obs_type, exptime)
    else:
        x, y = xy

    logger.info('centering', 'Centering on Camera using Tip-Tilt Mirror')

    for i in range(max_iter):
        dx = config.Camera.center_x - x
        dy = config.Camera.center_y - y
        error = np.sqrt(dx**2 + dy**2)

        if error <= config.Centering.camera_with_ttm_precision:
            break

        _check_abort()

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info('centering',
                    f'Centering step {i+1}, error = {error:.1f} px')

        offsets.camera_to_ttm(dx, dy)

        x, y = _get_star(obs_type, exptime)
    else:
        raise CenteringMaxIter

    logger.info(
        'centering',
        f'Centered on Camera using Tip-Tilt Mirror, error = {error:.1f} px')
    return x, y


def on_wfs_with_ttm(max_iter: int = config.Centering.
                    camera_with_calibunit_max_iter,
                    timeout: float = np.inf) -> tuple[float, float]:
    logger.info('centering', 'Centering on WFS using Tip-Tilt Mirror')

    slopes_fps = toolbox.open_fps_once(config.FPS.SHWFS)

    if slopes_fps is None:
        logger.error('centering', f'{config.FPS.SHWFS} is missing')
        return np.nan, np.nan

    for i in range(max_iter):
        dx = -slopes_fps.get_param('slope_x_avg')
        dy = -slopes_fps.get_param('slope_y_avg')
        error = np.sqrt(dx**2 + dy**2)

        if error <= config.Centering.wfs_with_ttm_precision:
            break

        _check_abort()

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info('centering',
                    f'Centering step {i+1}, error = {error:.3f} px')

        offsets.wfs_to_ttm(dx, dy)
    else:
        raise CenteringMaxIter

    logger.info(
        'centering',
        f'Centered on WFS using Tip-Tilt Mirror, error = {error:.3f} px')
    return -dx, -dy


def _check_abort() -> ReturnCode:
    if database.get_last_value('obs',
                               'sequencer_status') == SequencerStatus.ABORTING:
        raise AbortRequested

    return ReturnCode.CENTERING_OK


def _get_star(obs_type: ObservationType,
              exptime: float) -> tuple[float, float]:
    img_path = camera.take_image(obs_type, exptime=exptime,
                                 comment="Centering sequence")

    if img_path is None:
        raise CameraTakeImageFailed

    img = fits.getdata(img_path)

    star = starfinder.find_star(img)

    if star is None:
        raise CenteringStarNotFound

    return star.x, star.y
