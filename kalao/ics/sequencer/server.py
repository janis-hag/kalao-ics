#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import functools
import logging
import os
import signal
import threading
from datetime import datetime, timezone
from types import FrameType
from typing import Any, Callable

from astropy import units as u
from astropy.coordinates import SkyCoord

from flask import Flask, Response, jsonify, request

from kalao.common.dataclasses import Template
from kalao.common.enums import (ReturnCode, SequencerStatus, ShutterStatus,
                                TemplateID)
from kalao.common.exceptions import (AbortRequested, MissingKeyword,
                                     SequencerException)

from kalao.ics import database, euler, ippower, logger, memory, services
from kalao.ics.hardware import (adc, calibunit, camera, cooling, filterwheel,
                                flipmirror, laser, shutter, tungsten)
from kalao.ics.sequencer import centering, seq_utils, templates
from kalao.ics.utils import background

import config

sigint_orig_handler = None
sigterm_orig_handler = None

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def sig_handler(signum: int, frame: FrameType | None) -> None:
    logger.info('sequencer', 'SIGTERM, SIGINT or CTRL-C received, exiting.')

    abort()

    memory.unlock('sequencer_lock', force=True)

    seq_utils.set_sequencer_status(SequencerStatus.OFF)
    logger.info('sequencer', 'Sequencer server off')

    if signum == signal.SIGINT:
        handler = sigint_orig_handler
    elif signum == signal.SIGTERM:
        handler = sigterm_orig_handler
    else:
        handler = None

    if handler is None:
        pass
    elif callable(handler):
        handler(signum, frame)
    elif handler == signal.SIG_DFL:
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)


def init() -> ReturnCode:
    logger.info(
        'sequencer',
        f'Starting KalAO Instrument Control Software (KalAO-ICS), version {config.version}'
    )

    logger.info('sequencer', 'Server initialisation')

    init_list = [
        ippower.init,
        services.init,
        calibunit.init,
        functools.partial(adc.init, config.PLC.Node.ADC1),
        functools.partial(adc.init, config.PLC.Node.ADC2),
        shutter.init,
        flipmirror.init,
        tungsten.init,
        laser.init,
        filterwheel.init,
        cooling.init,
    ]

    background.launch('sequencer', init_list, config.Sequencer.init_timeout)

    return ReturnCode.SEQ_OK


@app.after_request
def after_request(response: Response) -> Response:
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers[
        'Access-Control-Allow-Methods'] = 'GET, POST, DELETE, PUT, PATCH'
    response.headers[
        'Access-Control-Allow-Headers'] = 'Accept, Content-Type, Authorization'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    return response


@app.route('/ping')
def ping() -> str:
    return 'Pong'


@app.route('/status')
def status() -> Response:
    status = {
        'status': 'TEST',
        'nexp': 1,
        'nexp_tot': 1,
        'elapsed_time': 0,
        'exposure_time': 5,
    }

    return jsonify(status)


@app.route('/on_target', methods=['POST'])
def on_target() -> str:
    args = request.json

    database.store('obs', {
        'tcs_header_path': args['tcs_header_path'],
        'sequencer_on_target': True
    })

    return 'OK'


@app.route('/abort', methods=['POST'])
def abort() -> str:
    if not memory.locked('sequencer_lock'):
        return 'Nothing to abort'

    seq_utils.set_sequencer_status(SequencerStatus.ABORTING_USER)
    logger.info('sequencer', 'Received an abort request, aborting sequence.')

    centering.invalidate_manual_centering()

    if camera.cancel() != ReturnCode.OK:
        logger.error('sequencer', 'Failed to send cancel order to camera.')

    return 'Abort executed'


@app.route('/observation_block', methods=['POST'])
def observation_block() -> str | tuple[str, int]:
    # Parse json first
    args = request.json

    lock_secret = memory.lock('sequencer_lock')
    if lock_secret is None:
        return 'A sequence is already running', 409

    try:
        th = threading.Thread(target=_execute_observation_block, kwargs={})
        th.start()

        return 'Observation block launched'

    except Exception:
        memory.unlock('sequencer_lock', lock_secret)
        return 'An exception occurred', 500


@app.route('/template/<id>', methods=['POST'])
def template(id: str) -> str | tuple[str, int]:
    if not hasattr(templates, id) or id.startswith('_'):
        return 'Unknown template', 404

    # Parse json first
    args = request.json

    lock_secret = memory.lock('sequencer_lock')
    if lock_secret is None:
        return 'A sequence is already running', 409

    try:
        if 'type' in args:
            database.store(
                'obs', {
                    'sequencer_command_received': args,
                    'sequencer_obs_type': args['type']
                })
        else:
            database.store('obs', {'sequencer_command_received': args})

        if 'alphacat' in args and 'deltacat' in args:
            coord = SkyCoord(ra=args['alphacat'], dec=args['deltacat'],
                             unit=(u.hourangle, u.deg), frame='fk5')

            database.store('obs', {
                'target_ra': coord.ra.deg,
                'target_dec': coord.dec.deg
            })

            # Pre-configure ADCs
            zenith_angle = euler.telescope_zenith_angle(coord)
            adc.configure(zenith_angle=zenith_angle, blocking=False)

        logger.info('sequencer', f'Starting template {id}')

        kwargs = {
            'id': id,
            'func': getattr(templates, id),
            'args': args,
            'lock_secret': lock_secret
        }

        if id.startswith('KAO_'):
            th = threading.Thread(target=_execute_template, kwargs=kwargs)
            th.start()
        else:
            _execute_template(**kwargs)

        return 'Template launched'

    except Exception as exc:
        memory.unlock('sequencer_lock', lock_secret)

        logger.exception('sequencer', exc)

        return 'An exception occurred', 500


def _execute_observation_block(templates_list: list) -> ReturnCode:
    return ReturnCode.OK


def _execute_template(id: str, func: Callable, args: dict[str, Any],
                      lock_secret: str | None = None,
                      update_status: bool = True) -> ReturnCode:
    try:
        template = Template(id=TemplateID(id),
                            start=datetime.now(timezone.utc))

        memory.hdel('sequencer', 'error')

        # TODO: remove some after EULER-J
        if id == TemplateID.FOCUS:
            template.nexp = config.Focusing.nexp
        elif id == TemplateID.TARGET_OBSERVATION:
            template.nexp = 1
        elif 'nbPic' in args:
            template.nexp = args['nbPic']

        seq_utils.set_sequencer_status(SequencerStatus.SETUP)

        template.to_memory()

        func(template, **args)

    except AbortRequested:
        status = seq_utils.get_sequencer_status()

        if status == SequencerStatus.ABORTING_USER:
            logger.info('sequencer', f'Template {id} aborted on request')

            ret = ReturnCode.SEQ_OK

        else:
            logger.error('sequencer', f'Template {id} aborted by software')
            memory.hset('sequencer', 'error', 'Aborted by software')

            ret = ReturnCode.SEQ_ERROR

    except SequencerException as e:
        if update_status:
            seq_utils.set_sequencer_status(SequencerStatus.ERROR)

        if isinstance(e, MissingKeyword):
            logger.error(
                'sequencer',
                f'"{e.__doc__} ({e.args[0]})" happened during template {id}')
        else:
            logger.error('sequencer',
                         f'"{e.__doc__}" happened during template {id}')

        memory.hset('sequencer', 'error', e.__doc__)

        ret = ReturnCode.SEQ_ERROR

    except Exception as e:

        logger.error('sequencer',
                     f'Unexpected exception occurred during template {id}')
        logger.exception('sequencer', e)

        memory.hset('sequencer', 'error', 'Unexpected exception')

        ret = ReturnCode.SEQ_ERROR

    else:
        logger.info('sequencer', f'Template {id} ended')

        ret = ReturnCode.SEQ_OK

    # Close shutter in case there was an error
    if ret == ReturnCode.SEQ_ERROR and shutter.close() != ShutterStatus.CLOSED:
        logger.error('sequencer', 'Failed to close the shutter after error')

    if update_status:
        if ret == ReturnCode.SEQ_ERROR:
            seq_utils.set_sequencer_status(SequencerStatus.ERROR)
        else:
            seq_utils.set_sequencer_status(SequencerStatus.WAITING)

    if lock_secret is not None:
        memory.unlock('sequencer_lock', lock_secret)

    return ret


if __name__ == '__main__':
    memory.flush()

    seq_utils.set_sequencer_status(SequencerStatus.INITIALISING)

    sigint_orig_handler = signal.signal(signal.SIGINT, sig_handler)
    sigterm_orig_handler = signal.signal(signal.SIGTERM, sig_handler)

    init()

    memory.unlock('sequencer_lock', force=True)

    seq_utils.set_sequencer_status(SequencerStatus.WAITING)
    logger.info('sequencer', 'Server on')

    app.run(host='0.0.0.0', port=config.Sequencer.port, threaded=True,
            debug=False)
