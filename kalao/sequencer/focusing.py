import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from astropy.io import fits

from kalao import database, logger
from kalao.fli import camera
from kalao.interfaces import etcs
from kalao.sequencer.seq_context import with_sequencer_status
from kalao.utils import file_handling, starfinder

from kalao.definitions.enums import ObservationType, SequencerStatus

import config


@with_sequencer_status(SequencerStatus.FOCUSING)
def focus_sequence(steps=config.Focusing.steps,
                   step_size=config.Focusing.step_size,
                   dit=config.Focusing.dit, window_size=80, abort_queue=None):
    """
    Starts a sequence to find best telescope M2 focus position.

    TODO normalise flux by integration time and adapt focusing_dit in case of saturation

    :param sequencer_arguments:
    :param steps: number of points to take for in the sequence
    :param dit: integration time for each image
    :return:
    """

    # TODO: dit optimization

    initial_focus = etcs.get_focus()
    focus_start = initial_focus - steps/2*step_size
    focus_stop = initial_focus + steps/2*step_size

    focus_sequence = np.linspace(focus_start, focus_stop, steps)

    data = pd.DataFrame(columns=['focus', 'x', 'y', 'peak', 'fwhm'])

    with open('/tmp/focus_sequence.fits',
              'w+b') as file, fits.open(file, 'update') as hdul:
        hdul.append(fits.PrimaryHDU())
        hdul.flush()

        for step, focus in enumerate(focus_sequence):
            # Check if an abort was requested
            if abort_queue is not None and not abort_queue.empty():
                logger.info('focusing', 'Focus sequence aborted on request')
                hdul[0].header.set('HIERARCH FOCUS SUCCESS', False,
                                   'Abort requested')
                hdul.flush()
                return -1

            etcs.set_focus(focus)

            filepath = camera.take_image(ObservationType.FOCUS, dit=dit)

            file_handling.add_comment(
                filepath, f'Focus sequence {step+1}/{steps}: focus={focus}µm')

            img = fits.getdata(filepath)

            x_star, y_star, peak, fwhm = starfinder.find_star(img)

            if np.isnan([x_star, y_star, peak, fwhm]).any():
                logger.error('focusing',
                             'Focus sequence aborted, star not found')
                hdul[0].header.set('HIERARCH FOCUS SUCCESS', False,
                                   'Star not found')
                hdul.flush()
                return -1

            data.loc[step] = {
                'focus': focus,
                'x': x_star,
                'y': y_star,
                'peak': peak,
                'fwhm': fwhm
            }

            img_cut = img[y_star - window_size//2:y_star + window_size//2,
                          x_star - window_size//2:x_star + window_size//2]

            hdu = fits.ImageHDU(img_cut, name=f'FOCUS{step+1}')
            hdu.header.set('HIERARCH FOCUS M2 POSITION', focus, '[um]')
            hdu.header.set('HIERARCH FOCUS STAR X', x_star, '[px]')
            hdu.header.set('HIERARCH FOCUS STAR Y', y_star, '[px]')
            hdu.header.set('HIERARCH FOCUS STAR PEAK', peak, '[ADU]')
            hdu.header.set('HIERARCH FOCUS STAR FWHM', fwhm, '[px]')
            hdu.header.set('HIERARCH FOCUS PATH', filepath, '')
            hdul.append(hdu)

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
                f'Focus sequence {step+1}/{steps}: focus={focus}µm, x={x_star}px, y={y_star}px, peak={peak}ADU, FWHM={fwhm}px'
            )

        idxmin = data['fwhm'].idxmin()

        if idxmin == 0 or idxmin == len(focus_sequence):
            logger.error('focusing', 'No minima found during focus sequence')

            best_focus = data['focus'][idxmin]
            best_fwhm = fit(best_focus)

            hdul[0].header.set('HIERARCH FOCUS BEST M2 POSITION', best_focus,
                               '[um] Best focus (estimated using fit)')
            hdul[0].header.set('HIERARCH FOCUS BEST STAR FWHM', best_fwhm,
                               '[px] Best focus FWHM (estimated using fit)')
            hdul[0].header.set('HIERARCH FOCUS SUCCESS', False,
                               'No minima reached')
            hdul.flush()

            # Set focus to minimum value found anyway
            etcs.set_focus(best_focus)

            database.store('obs', {
                'focusing_best': best_focus,
            })

            return -1

        best_focus = -b / (2*a)
        best_fwhm = fit(best_focus)

        logger.info('focusing', f'Best focus found at {best_focus} µm')

        hdul[0].header.set('HIERARCH FOCUS BEST M2 POSITION', best_focus,
                           '[um] Best focus (estimated using fit)')
        hdul[0].header.set('HIERARCH FOCUS BEST STAR FWHM', best_fwhm,
                           '[px] Best focus FWHM (estimated using fit)')
        hdul[0].header.set('HIERARCH FOCUS SUCCESS', True, '')
        hdul.flush()

        etcs.set_focus(best_focus)

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

    return 0


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

    if f1 == {} or (datetime.now(timezone.utc) - f0['timestamp']
                    ).total_seconds() > config.Focusing.autofocus_max_age:
        f1 = config.Focusing.autofocus_f1
    else:
        f1 = f1['value']

    focus = f0 + f1 * (temttb-1.2+temtth) / 2

    logger.info('focusing', f'Autofocus: setting focus to {focus} µm')

    etcs.set_focus(focus)


def update_autofocus_model(focus, temttb, temtth):
    f1 = config.Focusing.autofocus_f1
    f0 = focus - f1 * (temttb-1.2+temtth) / 2

    return f0, f1
