import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from astropy.io import fits

from kalao import database, logger
from kalao.fli import camera
from kalao.interfaces import etcs
from kalao.plc import filterwheel
from kalao.sequencer.seq_context import with_sequencer_status
from kalao.utils import file_handling, starfinder

from kalao.definitions.enums import (ObservationType, ReturnCode,
                                     SequencerStatus)
from kalao.definitions.exceptions import (AbortRequested, FLITakeImageFailed,
                                          FocusingException,
                                          FocusingInvertedCurve,
                                          FocusingMinimaOutsideRange,
                                          FocusingNoMinima, FocusingSaturated,
                                          FocusingStarNotFound)

import config


@with_sequencer_status(SequencerStatus.FOCUSING)
def focus_sequence(exptime, steps=config.Focusing.steps,
                   step_size=config.Focusing.step_size,
                   window_size=config.Focusing.window_size):
    """
    Starts a sequence to find best telescope M2 focus position.
    """

    filepath = file_handling.get_focus_sequence_filepath()

    initial_focus = etcs.get_focus()
    focus_start = initial_focus - steps/2*step_size
    focus_stop = initial_focus + steps/2*step_size

    focus_sequence = np.linspace(focus_start, focus_stop, steps)

    data = pd.DataFrame(columns=['focus', 'x', 'y', 'peak', 'fwhm'])

    symlink = config.FITS.last_focus_sequence
    symlink.unlink(missing_ok=True)
    symlink.symlink_to(filepath)

    with open(filepath, 'w+b') as file, fits.open(file, 'update') as hdul:
        try:
            filter = filterwheel.get_filter(type=str, from_db=True)

            hdu = fits.PrimaryHDU()
            hdu.header.set('HIERARCH FOCUS EXPTIME', exptime, '[s] Exposure time')
            hdu.header.set('HIERARCH FOCUS FILTER', filter, 'Filter name')
            hdul.append(hdu)
            hdul.flush()

            logger.info('focusing', 'Starting focus sequence')

            for step, focus in enumerate(focus_sequence):
                # Check if an abort was requested
                if database.get_last_value(
                        'sequencer_status') == SequencerStatus.ABORTING:
                    raise AbortRequested

                etcs.set_focus(focus)

                filepath = camera.take_image(ObservationType.FOCUS, exptime=exptime)

                if filepath is None:
                    raise FLITakeImageFailed

                file_handling.add_comment(
                    filepath,
                    f'Focus sequence {step+1}/{steps}: focus={focus:.2f}um')

                img = fits.getdata(filepath)

                star = starfinder.find_star(img)

                if star is None:
                    raise FocusingStarNotFound

                if star.peak >= 65535:
                    raise FocusingSaturated

                # Store star info for fitting
                data.loc[step] = {
                    'focus': focus,
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
                hdu.header.set('HIERARCH FOCUS M2 POSITION', focus, '[um]')
                hdu.header.set('HIERARCH FOCUS STAR X', star.x, '[px]')
                hdu.header.set('HIERARCH FOCUS STAR Y', star.y, '[px]')
                hdu.header.set('HIERARCH FOCUS STAR PEAK', star.peak, '[ADU]')
                hdu.header.set('HIERARCH FOCUS STAR FWHM', star.fwhm, '[px]')
                hdu.header.set('HIERARCH FOCUS FILE', filepath.stem, '')
                hdul.append(hdu)

                # If we have at least three points, start fitting a parabola
                if step >= 2:
                    x = data['focus'].to_numpy()
                    y = data['fwhm'].to_numpy()

                    fit = np.polynomial.polynomial.Polynomial.fit(x, y, 2)
                    c, b, a = fit.convert().coef

                    hdul[0].header.set('HIERARCH FOCUS FIT QUAD', a,
                                       '[1/um] Fit quadratic term')
                    hdul[0].header.set('HIERARCH FOCUS FIT LIN', b,
                                       '[-] Fit linear term')
                    hdul[0].header.set('HIERARCH FOCUS FIT CONST', c,
                                       '[um] Fit constant term')

                hdul.flush()

                logger.info(
                    'focusing',
                    f'Focus sequence {step+1}/{steps}: focus = {focus:.2f} µm, x = {star.x:.1f} px, y = {star.y:.1f} px, peak = {star.peak:.1f} ADU, FWHM = {star.fwhm:.2f} px'
                )

            # Check if we reached a minima
            idxmin = data['fwhm'].idxmin()

            # Determine best focus according to the fit
            best_focus = -b / (2*a)
            best_fwhm = fit(best_focus)

            if a <= 0:
                raise FocusingInvertedCurve

            elif idxmin == 0 or idxmin == len(focus_sequence) - 1:
                best_focus = data['focus'][idxmin]
                best_fwhm = fit(best_focus)

                hdul[0].header.set('HIERARCH FOCUS BEST M2 POSITION',
                                   best_focus, '[um] Best focus')
                hdul[0].header.set('HIERARCH FOCUS BEST STAR FWHM', best_fwhm,
                                   '[px] Best focus FWHM')

                # Set focus to minimum value found anyway
                etcs.set_focus(best_focus)

                database.store('obs', {
                    'focusing_best': best_focus,
                })

                raise FocusingNoMinima

            elif not focus_start <= best_focus <= focus_stop:
                raise FocusingMinimaOutsideRange

            logger.info('focusing', f'Best focus found at {best_focus} µm')

            hdul[0].header.set('HIERARCH FOCUS BEST M2 POSITION', best_focus,
                               '[um] Best focus (estimated using fit)')
            hdul[0].header.set('HIERARCH FOCUS BEST STAR FWHM', best_fwhm,
                               '[px] Best focus FWHM (estimated using fit)')
            hdul[0].header.set('HIERARCH FOCUS SUCCESS', True,
                               'Focus sequence successful')
            hdul.flush()

            etcs.set_focus(best_focus)
        except (FocusingException, AbortRequested, FLITakeImageFailed) as e:
            logger.error('focusing', f'Focus sequence aborted, "{e.__doc__}"')

            hdul[0].header.set('HIERARCH FOCUS SUCCESS', False,
                               'Focus sequence successful')
            hdul[0].header.set('HIERARCH FOCUS REASON', e.__doc__,
                               'Reason why focus sequence failed')
            hdul.flush()

            if not isinstance(e, FocusingNoMinima):
                # Restore focus
                logger.info('focusing', f'Restoring focus using autofocus')
                autofocus()

            return -1

    # Update autofocus
    temps = etcs.get_tube_temps()

    if (time.time() - int(temps['tunix'])) < config.ETCS.max_age:
        logger.info('focusing', 'Updated autofocusing model')

        f0, f1 = update_autofocus_model(best_focus, temps['temttb'],
                                        temps['temtth'])

        database.store(
            'obs', {
                'focusing_best': best_focus,
                'focusing_temttb': temps['temttb'],
                'focusing_temtth': temps['temtth'],
                'focusing_f0': f0,
                'focusing_f1': f1,
            })
    else:
        database.store('obs', {
            'focusing_best': best_focus,
        })

    return ReturnCode.FOCUSING_OK


def autofocus():
    temps = etcs.get_tube_temps()

    temttb = temps['temttb']
    temtth = temps['temtth']

    f0 = database.get_last('obs', 'focusing_f0')
    f1 = database.get_last('obs', 'focusing_f1')

    if f0 == {} or (datetime.now(timezone.utc) - f0['timestamp']
                    ).total_seconds() > config.Focusing.autofocus_max_age:
        f0 = config.Focusing.autofocus_f0
    else:
        f0 = f0['value']

    if f1 == {} or (datetime.now(timezone.utc) - f1['timestamp']
                    ).total_seconds() > config.Focusing.autofocus_max_age:
        f1 = config.Focusing.autofocus_f1
    else:
        f1 = f1['value']

    focus = f0 + f1 * (temttb-1.2+temtth) / 2

    logger.info('focusing', f'Autofocus: setting focus to {focus} µm')

    etcs.set_focus(focus)

    return ReturnCode.FOCUSING_OK


def update_autofocus_model(focus, temttb, temtth):
    f1 = config.Focusing.autofocus_f1
    f0 = focus - f1 * (temttb-1.2+temtth) / 2

    return f0, f1
