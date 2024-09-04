import time
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from astropy.io import fits

from kalao.common import spiral_search, starfinder
from kalao.common.dataclasses import Star, Template
from kalao.common.enums import (AdaptiveOpticsMode, CalibUnitPositionName,
                                CameraStatus, CenteringMode, FlipMirrorStatus,
                                ReturnCode, ShutterStatus, TemplateID,
                                WindowHint)
from kalao.common.exceptions import (AbortRequested, AutomaticCenteringTimeout,
                                     CameraTakeImageFailed, CenteringException,
                                     CenteringFluxWFSTooLow, CenteringMaxIter,
                                     CenteringOffsettingFailed,
                                     CenteringStarNotFound, DMNotOn,
                                     FilterWheelNotInPosition, FlipMirrorNotUp,
                                     ManualCenteringTimeout, ShutterNotClosed,
                                     WFSAcquisitionOff)
from kalao.common.json import KalAOJSONDecoder, KalAOJSONEncoder

from kalao.ics import database, logger, memory
from kalao.ics.cacao import aocontrol, toolbox
from kalao.ics.hardware import (calibunit, camera, dm, filterwheel, flipmirror,
                                laser, shutter, wfs)
from kalao.ics.sequencer import seq_utils
from kalao.ics.sequencer.seq_utils import WindowHintContextManager
from kalao.ics.utils import offsets

import config


@dataclass
class CenteringMetadata:
    template: Template
    star: Star | None = None


encoder = KalAOJSONEncoder()
decoder = KalAOJSONDecoder()


def center_on_target(
        exptime: float | None = None,
        centering_mode: CenteringMode = CenteringMode.AUTOMATIC,
        adaptiveoptics_mode: AdaptiveOpticsMode = AdaptiveOpticsMode.DISABLED,
        fallback_to_manual: bool = True) -> ReturnCode:
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
            if fallback_to_manual:
                logger.error(
                    'centering',
                    f'"{e.__doc__}" happened during centering on target, switching to manual centering'
                )

                # Will wait until manual centering is done, or raise an exception if manual centering timeout is reached
                request_manual_centering(template, reason=e.__doc__)
            else:
                logger.error(
                    'centering',
                    f'"{e.__doc__}" happened during centering on target')

                raise e

    else:
        logger.info('centering', 'Starting manual centering')

        # Take at least one image so the observer can click on it
        img_path = camera.take_science_image(template,
                                             comment="Manual centering")

        if img_path is None:
            raise CameraTakeImageFailed

        # Will wait until manual centering is done, or raise an exception if manual centering timeout is reached
        request_manual_centering(template, reason='Requested by observer')

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


def do_spiral_search(exptime: float | None = None,
                     overlap: float = config.SpiralSearch.overlap
                     ) -> ReturnCode:
    logger.info(
        'centering',
        f'Starting spiral search with an overlap of {overlap * 100:.0f}%.')

    template = Template(id=TemplateID.TARGET_CENTERING,
                        start=datetime.now(timezone.utc))
    template.to_memory()

    memory.hmset(
        'spiral_search', {
            'radius': 1,
            'overlap': overlap,
            'expno': 0,
            'star_dx': np.nan,
            'star_dy': np.nan
        })

    with (WindowHintContextManager(WindowHint.SPIRAL_SEARCH)):
        coords = spiral_search.generate_grid(overlap=overlap, radius=1)
        expno = 0
        coord = coords[0]

        # Note: we assume that there was no star in the initial field

        while True:
            try:
                if seq_utils.is_aborting():
                    raise AbortRequested

                expno += 1

                if expno == len(coords):
                    coords = spiral_search.generate_grid(
                        overlap=overlap, radius=coord.radius + 1)

                prev_coord = coord
                coord = coords[expno]

                dx = coord.dx - prev_coord.dx
                dy = coord.dy - prev_coord.dy

                logger.info('centering', f'Spiral search step {expno}.')

                if offsets.camera_to_telescope(dx, dy) != ReturnCode.OK:
                    raise CenteringOffsettingFailed

                star = _get_star(template, exptime, comment='Spiral search')

            except CenteringStarNotFound:
                memory.hmset('spiral_search', {
                    'radius': coord.radius,
                    'expno': expno,
                })

            else:
                dx = config.Camera.center_x - star.x
                dy = config.Camera.center_y - star.y

                logger.info('centering',
                            'Spiral search: star found, final centering')

                if offsets.camera_to_telescope(dx, dy) != ReturnCode.OK:
                    raise CenteringOffsettingFailed

                tot_dx = coord.dx + dx
                tot_dy = coord.dy + dy

                logger.info(
                    'centering',
                    f'Spiral search: found star in the field of view at alt = {+tot_dx*config.Offsets.camera_x_to_tel_alt:.2f}" and az = {+tot_dy*config.Offsets.camera_y_to_tel_az:.2f}".'
                )

                memory.hmset(
                    'spiral_search', {
                        'radius': coord.radius,
                        'expno': expno,
                        'star_dx': tot_dx,
                        'star_dy': tot_dy
                    })

                # Update image
                camera.take_science_image(template, comment="Spiral search")

                return ReturnCode.CENTERING_OK


def request_manual_centering(template: Template,
                             reason: str = '') -> ReturnCode:
    logger.info('centering', 'Starting manual centering.')
    set_manual_centering_flag(True)

    memory.hmset(
        'centering_manual', {
            'template': encoder.encode(template),
            'timeout': time.time() + config.Centering.manual_timeout,
            'reason': reason
        })

    timeout = time.monotonic() + config.Centering.manual_timeout

    while time.monotonic() < timeout:
        if seq_utils.is_aborting():
            invalidate_manual_centering()
            raise AbortRequested

        elif get_manual_centering_flag() is False:
            break

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
    return memory.hget('centering_manual', 'flag', type=bool, default=False)


def set_manual_centering_flag(flag: bool) -> None:
    memory.hset('centering_manual', 'flag', flag)
    database.store('obs', {'centering_manual_flag': flag})

    if not flag:
        memory.hdel('centering_manual', 'template')


def manual_centering(dx: float, dy: float) -> ReturnCode:
    if camera.get_camera_status() != CameraStatus.IDLE:
        logger.warn(
            'centering',
            'Manual centering offsets ignored, exposure ongoing or camera unavailable.'
        )

    template_encoded = memory.hget('centering_manual', 'template')
    if template_encoded is None:
        template = Template(id=TemplateID.TARGET_CENTERING,
                            start=datetime.now(timezone.utc))
    else:
        template = decoder.decode(template_encoded)

    if offsets.camera_to_telescope(dx, dy) != ReturnCode.OK:
        raise CenteringOffsettingFailed

    img_path = camera.take_science_image(template, comment="Manual centering")

    if img_path is None:
        raise CameraTakeImageFailed

    memory.hset('centering_manual', 'template', encoder.encode(template))

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
