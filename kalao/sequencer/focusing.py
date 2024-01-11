import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from astropy.io import fits

from kalao import database, logger
from kalao.fli import camera
from kalao.interfaces import etcs
from kalao.utils import file_handling, starfinder

import config


def focus_sequence(steps=config.Focusing.steps,
                   step_size=config.Focusing.step_size,
                   dit=config.Focusing.dit, sequencer_arguments=None):
    """
    Starts a sequence to find best telescope M2 focus position.

    TODO normalise flux by integration time and adapt focusing_dit in case of saturation
    TODO handle abort of sequence

    :param sequencer_arguments:
    :param steps: number of points to take for in the sequence
    :param dit: integration time for each image
    :return:
    """

    if sequencer_arguments is None:
        q = None
    else:
        q = sequencer_arguments.get('q')

    # TODO: dit optimization

    initial_focus = etcs.get_focus()
    focus_start = initial_focus - steps/2*step_size
    focus_stop = initial_focus + steps/2*step_size

    focus_sequence = np.linspace(focus_start, focus_stop, steps)

    data = pd.DataFrame({'focus': focus_sequence},
                        columns=['focus', 'x', 'y', 'peak', 'fwhm'])

    for step, focus in enumerate(focus_sequence):
        # Check if an abort was requested
        if q is not None and not q.empty():
            q.get()
            return -1

        etcs.set_focus(focus)

        file_path = camera.take_image(dit=dit,
                                      sequencer_arguments=sequencer_arguments)

        file_handling.add_comment(
            file_path, f'Focus sequence {step+1}/{steps}: focus={focus}µm')

        image = fits.getdata(file_path)

        x_star, y_star, peak, fwhm = starfinder.find_star(image)

        data.iloc[step] = {
            'focus': focus,
            'x': x_star,
            'y': y_star,
            'peak': peak,
            'fwhm': fwhm
        }

        logger.info(
            'focusing',
            f'Focus sequence {step+1}/{steps}: focus={focus}µm, x={x_star}px, y={y_star}px, peak={peak}ADU, FWHM={fwhm}px'
        )

    data = data.apply(pd.to_numeric)

    idxmin = data['fwhm'].idxmin()

    if idxmin == 0 or idxmin == len(focus_sequence):
        logger.error('focusing', 'No minima found during focus sequence')
        return -1

    x = data['focus'].to_numpy()
    y = data['fwhm'].to_numpy()

    fit = np.polynomial.polynomial.Polynomial.fit(x, y, 2)
    a, b, c = fit.coef

    best_focus = -b / 2 * a
    best_fwhm = fit(x)

    logger.info('focusing', f'Best focus found at {best_focus} µm')

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

    if f0 is None:
        f0 = config.Focusing.autofocus_f0

    if f1 is None:
        f1 = config.Focusing.autofocus_f1

    focus = f0 + f1 * (temttb-1.2+temtth) / 2

    logger.info('focusing', f'Autofocus: setting focus to {focus} µm')

    etcs.set_focus(focus)


def update_autofocus_model(focus, temttb, temtth):
    f1 = config.Focusing.autofocus_f1
    f0 = focus - f1 * (temttb-1.2+temtth) / 2

    return f0, f1


def get_latest_fo_delta():

    fo_delta_record = database.get_last('obs', 'focusing_fo_delta')

    if fo_delta_record.get('value') is None:
        return None

    fo_delta_age = (datetime.now(timezone.utc) -
                    fo_delta_record['timestamp']).total_seconds()

    if fo_delta_age > 12 * 3600:
        return None
    else:
        return fo_delta_record['value']
