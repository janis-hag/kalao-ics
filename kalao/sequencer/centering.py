import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

import numpy as np

from astropy.io import fits

from kalao import database, logger, memory
from kalao.cacao import aocontrol, toolbox
from kalao.hardware import (calibunit, camera, dm, filterwheel, flipmirror,
                            laser, shutter, wfs)
from kalao.sequencer import seq_utils
from kalao.utils import offsets, starfinder
from kalao.utils.json import KalAOJSONDecoder, KalAOJSONEncoder

from kalao.definitions.dataclasses import Star, Template
from kalao.definitions.enums import (AdaptiveOpticsMode, CalibUnitPositionName,
                                     CameraStatus, CenteringMode,
                                     FlipMirrorStatus, ReturnCode,
                                     ShutterStatus, TemplateID)
from kalao.definitions.exceptions import (
    AbortRequested, AutomaticCenteringTimeout, CameraTakeImageFailed,
    CenteringException, CenteringFluxWFSTooLow, CenteringMaxIter,
    CenteringOffsettingFailed, CenteringStarNotFound, DMNotOn,
    FilterWheelNotInPosition, FlipMirrorNotUp, ManualCenteringTimeout,
    ShutterNotClosed, WFSAcquisitionOff)

import config


class Direction(StrEnum):
    TOP = 'TOP'
    RIGHT = 'RIGHT'
    BOTTOM = 'BOTTOM'
    LEFT = 'LEFT'


_spiral_next_mapping = {
    Direction.TOP: Direction.RIGHT,
    Direction.RIGHT: Direction.BOTTOM,
    Direction.BOTTOM: Direction.LEFT,
    Direction.LEFT: Direction.TOP,
}


@dataclass
class CenteringMetadata:
    template: Template
    star: Star | None = None


encoder = KalAOJSONEncoder()
decoder = KalAOJSONDecoder()


def center_on_target(
    exptime: float | None = None,
    centering_mode: CenteringMode = CenteringMode.AUTOMATIC,
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

    template = Template(id=TemplateID.TARGET_CENTERING,
                        start=datetime.now(timezone.utc))
    template.to_memory()

    timeout = time.monotonic() + config.Centering.automatic_timeout

    if centering_mode == CenteringMode.AUTOMATIC:
        logger.info('centering', 'Starting automatic centering')

        try:
            md = CenteringMetadata(template=template,
                                   star=_get_star(template, exptime))

            on_camera_with_telescope(exptime=exptime, md=md, timeout=timeout)
            on_camera_with_ttm(exptime=exptime, md=md, timeout=timeout)

        except (AbortRequested, CameraTakeImageFailed) as e:
            logger.error('centering',
                         f'"{e.__doc__}" happened during centering on target')

            raise e

        except CenteringException as e:
            logger.error(
                'centering',
                f'"{e.__doc__}" happened during centering on target, switching to manual centering'
            )

            # Will wait until manual centering is done, or raise an exception if manual centering timeout is reached
            request_manual_centering(template)

    else:
        logger.info('centering', 'Starting manual centering')

        # Take at least one image so the observer can click on it
        img_path = camera.take_science_image(template,
                                             comment="Manual centering")

        if img_path is None:
            raise CameraTakeImageFailed

        # Will wait until manual centering is done, or raise an exception if manual centering timeout is reached
        request_manual_centering(template)

    if adaptiveoptics_mode == AdaptiveOpticsMode.ENABLED:
        # Check if enough light is on the WFS for precise centering
        if wfs.optimize_flux() != ReturnCode.OK:
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

    if shutter.close() != ShutterStatus.CLOSED:
        raise ShutterNotClosed

    if flipmirror.up() != FlipMirrorStatus.UP:
        raise FlipMirrorNotUp

    template = Template(id=TemplateID.LASER_CENTERING,
                        start=datetime.now(timezone.utc))
    template.to_memory()

    md = CenteringMetadata(template=template)

    if not wfs.check_flux():
        # Move calib unit to approximately correct position if too far
        if calibunit.get_position_name() != CalibUnitPositionName.LASER:
            calibunit.move_to_laser_position()

        if filterwheel.set_filter(config.Camera.laser_calib_filter
                                  ) != config.Camera.laser_calib_filter:
            raise FilterWheelNotInPosition

        laser.set_power(config.Camera.laser_calib_power, enable=True)

        # Reset tip tilt stream to 0
        aocontrol.reset_dm(config.AO.TTM_loop_number)

        try:
            md.star = _get_star(template, config.Camera.laser_calib_exptime)

            on_camera_with_calibunit(exptime=config.Camera.laser_calib_exptime,
                                     md=md)
            on_camera_with_ttm(exptime=config.Camera.laser_calib_exptime,
                               md=md)
        except (CenteringException, AbortRequested,
                CameraTakeImageFailed) as e:
            logger.error('centering',
                         f'"{e.__doc__}" happened during centering on laser')
            return ReturnCode.CENTERING_ERROR

        # Precise centering with WFS
        wfs.emgain_off()

        laser.set_power(config.WFS.laser_calib_power, enable=True)
        wfs.set_exptime(config.WFS.laser_calib_exptime)
        wfs.set_emgain(config.WFS.laser_calib_emgain)

    try:
        on_wfs_with_ttm(md=md)
    except (CenteringException, AbortRequested, CameraTakeImageFailed) as e:
        logger.error('centering',
                     f'"{e.__doc__}" happened during centering on laser')
        return ReturnCode.CENTERING_ERROR

    logger.info('centering', 'Centering done')

    return ReturnCode.CENTERING_OK


def spiral_search(exptime: float | None = None, overlap: float = 0.25,
                  direction: Direction = Direction.TOP,
                  max_turns: int = sys.maxsize) -> ReturnCode:
    logger.info(
        'centering',
        f'Starting spiral search with an overlap of {overlap * 100:.0f}%.')

    template = Template(id=TemplateID.TARGET_CENTERING,
                        start=datetime.now(timezone.utc))
    template.to_memory()

    tot_dx = 0
    tot_dy = 0

    max_exps = 4*max_turns + 1

    while template.expno < max_exps:
        tot = template.expno // 2 + 1

        for s in range(tot):
            try:
                star = _get_star(template, exptime, comment='Spiral search')
            except CenteringStarNotFound:
                pass
            else:
                dx = config.Camera.center_x - star.x
                dy = config.Camera.center_y - star.y

                logger.info('centering',
                            'Spiral search: star found, final centering')

                if offsets.camera_to_telescope(dx, dy) != ReturnCode.OK:
                    raise CenteringOffsettingFailed

                tot_dx += dx
                tot_dy += dy

                logger.info(
                    'centering',
                    f'Spiral search: found star in the field of view at alt = {+tot_dx*config.Offsets.camera_x_to_tel_alt:.2f}" and az = {+tot_dy*config.Offsets.camera_y_to_tel_az:.2f}".'
                )

                # Update image
                camera.take_science_image(template, comment="Spiral search")

                return ReturnCode.CENTERING_OK

            dx = 1024 * (1-overlap)
            dy = 1024 * (1-overlap)

            match direction:
                case Direction.TOP:
                    dx = 0
                    # dy positive
                case Direction.RIGHT:
                    dx *= -1
                    dy = 0
                case Direction.BOTTOM:
                    dx = 0
                    dy *= -1
                case Direction.LEFT:
                    # dx positive
                    dy = 0

            logger.info(
                'centering',
                f'Spiral search step {template.expno}: moving {direction} ({s+1}/{tot}).'
            )

            if offsets.camera_to_telescope(dx, dy) != ReturnCode.OK:
                raise CenteringOffsettingFailed

            tot_dx += dx
            tot_dy += dy

        direction = _spiral_next_mapping[direction]

    return ReturnCode.CENTERING_ERROR


def request_manual_centering(template: Template) -> ReturnCode:
    logger.info('centering', 'Starting manual centering.')
    set_manual_centering_flag(True)

    memory.hmset(
        'centering', {
            'template': encoder.encode(template),
            'timeout': time.time() + config.Centering.manual_timeout
        })

    timeout = time.monotonic() + config.Centering.manual_timeout

    while time.monotonic() < timeout:
        if get_manual_centering_flag() is False:
            break

        elif seq_utils.is_aborting():
            invalidate_manual_centering()
            raise AbortRequested

        time.sleep(1)
    else:
        logger.error('centering',
                     'Timeout while waiting for manual centering from user.')
        invalidate_manual_centering()
        raise ManualCenteringTimeout

    # If the user validated the centering before exposure ended, wait
    camera_status = camera.get_camera_status()
    while camera_status in [CameraStatus.EXPOSING, CameraStatus.READING_CCD]:
        time.sleep(1)

        if seq_utils.is_aborting():
            raise AbortRequested

        camera_status = camera.get_camera_status()

    return ReturnCode.CENTERING_OK


def validate_manual_centering() -> ReturnCode:
    flag = get_manual_centering_flag()

    if flag is not False:
        logger.info('centering', 'Manual centering done.')
        set_manual_centering_flag(False)

    return ReturnCode.CENTERING_OK


def invalidate_manual_centering() -> ReturnCode:
    flag = get_manual_centering_flag()

    if flag is not False:
        logger.info('centering', 'Manual centering cancelled.')
        set_manual_centering_flag(False)

    return ReturnCode.CENTERING_OK


def get_manual_centering_flag() -> bool:
    return memory.hget('centering', 'manual_flag', type=bool, default=False)


def set_manual_centering_flag(flag: bool) -> None:
    memory.hset('centering', 'manual_flag', flag)
    database.store('obs', {'centering_manual_flag': flag})

    if not flag:
        memory.hdel('centering', 'template')


def manual_centering(dx: float, dy: float) -> ReturnCode:
    if camera.get_camera_status() != CameraStatus.IDLE:
        logger.warn(
            'centering',
            'Manual centering offsets ignored, exposure ongoing or camera unavailable.'
        )

    template = decoder.decode(memory.hget('centering', 'template'))

    if template is None:
        template = Template(id=TemplateID.TARGET_CENTERING,
                            start=datetime.now(timezone.utc))

    if offsets.camera_to_telescope(dx, dy) != ReturnCode.OK:
        raise CenteringOffsettingFailed

    img_path = camera.take_science_image(template, comment="Manual centering")

    if img_path is None:
        raise CameraTakeImageFailed

    memory.hset('centering', 'template', encoder.encode(template))

    return ReturnCode.CENTERING_OK


def on_camera_with_calibunit(exptime: float, md: CenteringMetadata |
                             None = None, max_iter: int = config.Centering.
                             camera_with_calibunit_max_iter,
                             timeout: float = np.inf) -> None:
    logger.info('centering', 'Centering on camera using calib. unit')

    for _ in range(max_iter):
        dy = config.Camera.center_y - md.star.y
        error = np.abs(dy)

        if error <= config.Centering.camera_with_calibunit_precision:
            break

        if seq_utils.is_aborting():
            raise AbortRequested

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info(
            'centering',
            f'Centering step {md.template.expno}, on camera with calib. unit, error = {error:.2f} px'
        )

        if offsets.camera_to_calibunit(dy) != ReturnCode.OK:
            raise CenteringOffsettingFailed

        md.star = _get_star(md.template, exptime)
    else:
        raise CenteringMaxIter

    logger.info(
        'centering',
        f'Centered on camera using calib. unit, error = {error:.2f} px')


def on_camera_with_telescope(exptime: float, md: CenteringMetadata |
                             None = None, max_iter: int = config.Centering.
                             camera_with_calibunit_max_iter,
                             timeout: float = np.inf) -> None:
    if md.template.id == TemplateID.TARGET_CENTERING:
        scale = config.Camera.plate_scale
        unit = '"'
    else:
        scale = 1
        unit = ' px'

    logger.info('centering', 'Centering on camera using telescope')

    for _ in range(max_iter):
        dx = config.Camera.center_x - md.star.x
        dy = config.Camera.center_y - md.star.y
        error = np.sqrt(dx**2 + dy**2)

        if error <= config.Centering.camera_with_telescope_precision:
            break

        if seq_utils.is_aborting():
            raise AbortRequested

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info(
            'centering',
            f'Centering step {md.template.expno}, on camera with telescope, error = {error*scale:.2f}{unit}'
        )

        if offsets.camera_to_telescope(dx, dy) != ReturnCode.OK:
            raise CenteringOffsettingFailed

        md.star = _get_star(md.template, exptime)
    else:
        raise CenteringMaxIter

    logger.info(
        'centering',
        f'Centered on camera using telescope, error = {error*scale:.2f}{unit}')


def on_camera_with_ttm(exptime: float, md: CenteringMetadata | None = None,
                       max_iter: int = config.Centering.
                       camera_with_calibunit_max_iter,
                       timeout: float = np.inf) -> None:
    if md.template.id == TemplateID.TARGET_CENTERING:
        scale = config.Camera.plate_scale
        unit = '"'
    else:
        scale = 1
        unit = ' px'

    logger.info('centering', 'Centering on camera using tip-tilt mirror')

    for _ in range(max_iter):
        dx = config.Camera.center_x - md.star.x
        dy = config.Camera.center_y - md.star.y
        error = np.sqrt(dx**2 + dy**2)

        if error <= config.Centering.camera_with_ttm_precision:
            break

        if seq_utils.is_aborting():
            raise AbortRequested

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info(
            'centering',
            f'Centering step {md.template.expno}, on camera with tip-tilt mirror, error = {error*scale:.2f}{unit}'
        )

        if offsets.camera_to_ttm(dx, dy) != ReturnCode.OK:
            raise CenteringOffsettingFailed

        md.star = _get_star(md.template, exptime)
    else:
        raise CenteringMaxIter

    logger.info(
        'centering',
        f'Centered on camera using tip-tilt mirror, error = {error*scale:.2f}{unit}'
    )


def on_wfs_with_ttm(md: CenteringMetadata | None = None,
                    max_iter: int = config.Centering.
                    camera_with_calibunit_max_iter,
                    timeout: float = np.inf) -> None:
    if md.template.id == TemplateID.TARGET_CENTERING:
        scale = config.WFS.plate_scale
        unit = '"'
    else:
        scale = 1
        unit = ' px'

    logger.info('centering',
                'Centering on wavefront sensor using tip-tilt mirror')

    slopes_fps = toolbox.get_fps(config.FPS.SHWFS)

    if slopes_fps is None:
        logger.error('centering', f'{config.FPS.SHWFS} is missing')
        return

    for _ in range(max_iter):
        dx = -slopes_fps.get_param('slope_x_avg')
        dy = -slopes_fps.get_param('slope_y_avg')
        error = np.sqrt(dx**2 + dy**2)

        if error <= config.Centering.wfs_with_ttm_precision:
            break

        if seq_utils.is_aborting():
            raise AbortRequested

        if time.monotonic() > timeout:
            raise AutomaticCenteringTimeout

        logger.info(
            'centering',
            f'Centering step {md.template.expno}, on wavefront sensor with tip-tilt mirror, error = {error*scale:.2f}{unit}'
        )

        if offsets.wfs_to_ttm(dx, dy) != ReturnCode.OK:
            raise CenteringOffsettingFailed

        md.template.next_exposure()
    else:
        raise CenteringMaxIter

    logger.info(
        'centering',
        f'Centered on wavefront sensor using tip-tilt mirror, error = {error*scale:.2f}{unit}'
    )


def _get_star(template: Template, exptime: float | None,
              comment='Automatic centering') -> Star:
    img_path = camera.take_science_image(template, exptime=exptime,
                                         comment=comment)

    if img_path is None:
        raise CameraTakeImageFailed

    img = fits.getdata(img_path)

    star = starfinder.find_star(img)

    if star is None:
        raise CenteringStarNotFound

    return star
