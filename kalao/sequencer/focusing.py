import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from astropy.io import fits

from kalao import database, logger
from kalao.hardware import camera, filterwheel
from kalao.interfaces import etcs
from kalao.sequencer.seq_context import with_sequencer_status
from kalao.utils import file_handling, starfinder

from kalao.definitions.enums import (ObservationType, ReturnCode,
                                     SequencerStatus)
from kalao.definitions.exceptions import *

import config


@with_sequencer_status(SequencerStatus.FOCUSING)
def focus_sequence(exptime: float, steps: int = config.Focusing.steps,
                   step_size: float = config.Focusing.step_size,
                   window_size: int = config.Focusing.window_size
                   ) -> ReturnCode:
    """
    Starts a sequence to find best telescope M2 focus position.
    """

    filepath = file_handling.get_focus_sequence_filepath()

    initial_focus = etcs.get_focus()
    focus_start = initial_focus - steps/2*step_size
    focus_stop = initial_focus + steps/2*step_size

    m2_positions = np.linspace(focus_start, focus_stop, steps)

    data = pd.DataFrame(columns=['focus', 'x', 'y', 'peak', 'fwhm'])

    symlink = config.FITS.last_focus_sequence
    symlink.unlink(missing_ok=True)
    symlink.symlink_to(filepath)

    with open(filepath, 'w+b') as file, fits.open(file, 'update') as hdul:
        try:
            filter = filterwheel.get_filter(type=str, from_db=True)

            hdu = fits.PrimaryHDU()
            hdu.header.set('HIERARCH KAL FOC EXPTIME', exptime,
                           '[s] Exposure time')
            hdu.header.set('HIERARCH KAL FOC FILTER', filter, 'Filter name')
            hdul.append(hdu)
            hdul.flush()

            logger.info('focusing', 'Starting focus sequence')

            for step, m2_position in enumerate(m2_positions):
                # Check if an abort was requested
                if database.get_last_value(
                        'sequencer_status') == SequencerStatus.ABORTING:
                    raise AbortRequested

                etcs.set_focus(m2_position)

                filepath = camera.take_image(
                    ObservationType.FOCUS, exptime=exptime, comment=
                    f'Focus sequence {step+1}/{steps}, focus={m2_position:.2f}um'
                )

                if filepath is None:
                    raise CameraTakeImageFailed

                img = fits.getdata(filepath)

                star = starfinder.find_star(img, method='moments')

                if star is None:
                    raise FocusingStarNotFound

                if star.peak >= 65535:
                    raise FocusingSaturated

                # Store star info for fitting
                data.loc[step] = {
                    'focus': m2_position,
                    'x': star.x,
                    'y': star.y,
                    'peak': star.peak,
                    'fwhm': star.fwhm
                }

                # Store vignette and star info in FITS
                img_cut = img[round(star.y) - window_size//2:round(star.y) +
                              window_size//2,
                              round(star.x) - window_size//2:round(star.x) +
                              window_size//2]

                hdu = fits.ImageHDU(img_cut, name=f'FOCUS{step+1}')
                hdu.header.set('HIERARCH KAL FOC M2 POS', m2_position, '[um]')
                hdu.header.set('HIERARCH KAL FOC STAR X', star.x, '[px]')
                hdu.header.set('HIERARCH KAL FOC STAR Y', star.y, '[px]')
                hdu.header.set('HIERARCH KAL FOC STAR PEAK', star.peak,
                               '[ADU]')
                hdu.header.set('HIERARCH KAL FOC STAR FWHM', star.fwhm, '[px]')
                hdu.header.set('HIERARCH KAL FOC FILE', filepath.stem, '')
                hdul.append(hdu)

                # If we have at least three points, start fitting a parabola
                if step >= 2:
                    x = data['focus'].to_numpy()
                    y = data['fwhm'].to_numpy()

                    fit = np.polynomial.polynomial.Polynomial.fit(x, y, 2)
                    c, b, a = fit.convert().coef

                    hdul[0].header.set('HIERARCH KAL FOC FIT QUAD', a,
                                       '[1/um] Fit quadratic term')
                    hdul[0].header.set('HIERARCH KAL FOC FIT LIN', b,
                                       '[-] Fit linear term')
                    hdul[0].header.set('HIERARCH KAL FOC FIT CONST', c,
                                       '[um] Fit constant term')

                hdul.flush()

                logger.info(
                    'focusing',
                    f'Focus sequence {step+1}/{steps}: focus = {m2_position:.2f} µm, x = {star.x:.1f} px, y = {star.y:.1f} px, peak = {star.peak:.1f} ADU, FWHM = {star.fwhm:.2f} px'
                )

            # Check if we reached a minima
            idxmin = data['fwhm'].idxmin()

            # Determine best focus according to the fit
            best_focus = -b / (2*a)
            best_fwhm = fit(best_focus)

            if a <= 0:
                raise FocusingInvertedCurve

            elif idxmin == 0 or idxmin == len(m2_positions) - 1:
                best_focus = data['focus'][idxmin]
                best_fwhm = fit(best_focus)

                hdul[0].header.set('HIERARCH KAL FOC BEST M2 POS', best_focus,
                                   '[um] Best focus')
                hdul[0].header.set('HIERARCH KAL FOC BEST STAR FWHM',
                                   best_fwhm, '[px] Best focus FWHM')

                # Set focus to minimum value found anyway
                etcs.set_focus(best_focus)

                database.store('obs', {
                    'focusing_m2_position': best_focus,
                })

                raise FocusingNoMinima

            elif not focus_start <= best_focus <= focus_stop:
                raise FocusingMinimaOutsideRange

            logger.info('focusing', f'Best focus found at {best_focus:.2f} µm')

            hdul[0].header.set('HIERARCH KAL FOC BEST M2 POS', best_focus,
                               '[um] Best focus (estimated using fit)')
            hdul[0].header.set('HIERARCH KAL FOC BEST STAR FWHM', best_fwhm,
                               '[px] Best focus FWHM (estimated using fit)')
            hdul[0].header.set('HIERARCH KAL FOC SUCCESS', True,
                               'Focus sequence successful')
            hdul.flush()

            etcs.set_focus(best_focus)
        except (FocusingException, AbortRequested, CameraTakeImageFailed) as e:
            logger.error('focusing', f'Focus sequence aborted, "{e.__doc__}"')

            hdul[0].header.set('HIERARCH KAL FOC SUCCESS', False,
                               'Focus sequence successful')
            hdul[0].header.set('HIERARCH KAL FOC REASON', e.__doc__,
                               'Reason why focus sequence failed')
            hdul.flush()

            if not isinstance(e, FocusingNoMinima):
                # Restore focus
                logger.info('focusing', f'Restoring focus using autofocus')
                autofocus()

            # Seal focus sequence file
            filepath.chmod(config.FITS.file_mask)

            return ReturnCode.FOCUSING_ERROR

    # Seal focus sequence file
    filepath.chmod(config.FITS.file_mask)

    # Update autofocus
    temps = etcs.get_tube_temps()

    if (time.time() - int(temps['tunix'])) < config.ETCS.max_age:
        logger.info('focusing', 'Updated autofocusing model')

        f0, f1 = update_autofocus_model(best_focus, temps['temttb'],
                                        temps['temtth'])

        database.store(
            'obs', {
                'focusing_m2_position': best_focus,
                'focusing_temttb': temps['temttb'],
                'focusing_temtth': temps['temtth'],
                'focusing_f0': f0,
                'focusing_f1': f1,
            })
    else:
        database.store('obs', {
            'focusing_m2_position': best_focus,
        })

    return ReturnCode.FOCUSING_OK


def autofocus() -> ReturnCode:
    temps = etcs.get_tube_temps()

    temttb = temps['temttb']
    temtth = temps['temtth']

    f0_db = database.get_last('obs', 'focusing_f0')
    f1_db = database.get_last('obs', 'focusing_f1')

    if f0_db == {} or (datetime.now(timezone.utc) - f0_db['timestamp']
                       ).total_seconds() > config.Focusing.autofocus_max_age:
        f0 = config.Focusing.autofocus_f0
    else:
        f0 = f0_db['value']

    if f1_db == {} or (datetime.now(timezone.utc) - f1_db['timestamp']
                       ).total_seconds() > config.Focusing.autofocus_max_age:
        f1 = config.Focusing.autofocus_f1
    else:
        f1 = f1_db['value']

    focus = f0 + f1 * (temttb-1.2+temtth) / 2

    logger.info('focusing', f'Autofocus: setting focus to {focus:.2f} µm')

    etcs.set_focus(focus)

    return ReturnCode.FOCUSING_OK


def update_autofocus_model(focus: float, temttb: float,
                           temtth: float) -> tuple[float, float]:
    f1 = config.Focusing.autofocus_f1
    f0 = focus - f1 * (temttb-1.2+temtth) / 2

    return f0, f1
