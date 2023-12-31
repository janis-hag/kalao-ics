import time

import numpy as np
import pandas as pd

from astropy.io import fits

from kalao import database, logger
from kalao.fli import camera
from kalao.utils import file_handling, kalao_time

from tcs_communication import t120

from kalao.definitions.enums import SequencerStatus

import config


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
        database.store('obs', {'sequencer_status': SequencerStatus.ERROR})
        logger.error('sequencer', f'No flux detected on science camera')
        return -1

    focus_flux = pd.DataFrame({'set_focus': [initial_focus], 'flux': [flux]})

    # Get even number of focus_points in order to include 0 in the sequence.
    if (focus_points % 2) == 1:
        focus_points = focus_points + 1

    focusing_sequence = (np.arange(focus_points + 1) -
                         focus_points/2) * config.Starfinder.focusing_step

    for step, focus_offset in enumerate(focusing_sequence):
        database.store('obs', {
            'sequencer_status': f'Focus {step+1}:{len(focusing_sequence)}'
        })  #TODO: this is irregular, do better
        logger.info('sequencer', f'Focus {step+1}:{len(focusing_sequence)}')

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
        # TODO check what the new focus settling time is
        time.sleep(5)

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
    logger.info('sequencer', f'Best focus value: {best_focus}')

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

    if fo_delta_record.get('value') is None:
        return None

    fo_delta_age = (kalao_time.now() -
                    fo_delta_record['timestamp']).total_seconds()

    if fo_delta_age > 12 * 3600:
        return None
    else:
        return fo_delta_record['value']
