#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
import socket
import traceback
from functools import partial
from itertools import zip_longest
from threading import Thread
from types import FrameType
from typing import Any

from astropy import units as u
from astropy.coordinates import SkyCoord

from kalao import database, euler, logger, services
from kalao.plc import (adc, calibunit, filterwheel, flipmirror, laser, shutter,
                       tungsten)
from kalao.sequencer import commands
from kalao.utils import background
from kalao.utils.rprint import rprint

from kalao.definitions.enums import ReturnCode, SequencerStatus, ShutterState
from kalao.definitions.exceptions import *

import config

conn = None
socketSeq = None


def handler(signal_received: int, frame: FrameType | None) -> None:
    if signal_received == signal.SIGINT or signal_received == signal.SIGTERM:
        rprint('\nSIGTERM or SIGINT or CTRL-C detected. Exiting.')

        if conn is not None:
            conn.close()

        if socketSeq is not None:
            socketSeq.close()

        database.store('obs', {'sequencer_status': SequencerStatus.OFF})
        logger.info('sequencer', 'Sequencer server off')

        exit(0)


def init() -> ReturnCode:
    logger.info('sequencer', 'Server initialisation')

    init_list = [
        services.init,
        calibunit.init,
        partial(adc.init, config.PLC.Node.ADC1),
        partial(adc.init, config.PLC.Node.ADC2),
        shutter.init,
        flipmirror.init,
        tungsten.init,
        laser.init,
        filterwheel.init,
    ]

    background.launch('sequencer', init_list, config.SEQ.init_timeout)

    return ReturnCode.SEQ_OK


def serve() -> ReturnCode:
    """
    receive commands in string form through a socket.
    format them into a dictionary.
    create a thread to execute the command.

    :return:
    """

    global conn, socketSeq

    socketSeq = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketSeq.bind((config.SEQ.ip, config.SEQ.port))

    th = None

    database.store('obs', {'sequencer_status': SequencerStatus.WAITING})
    logger.info('sequencer', 'Server on')

    while True:
        socketSeq.listen()
        # Do NOT update sequencer_status
        logger.info('sequencer', 'Waiting on connection')

        conn, address = socketSeq.accept()

        command_raw = (conn.recv(4096)).decode("utf8")

        separator = command_raw[0]
        command_list = command_raw[1:].split(separator)

        command = command_list[0]
        arguments = command_list[1:]

        database.store('obs', {'sequencer_status': SequencerStatus.BUSY})
        logger.info('sequencer',
                    f'command=> {command} < arg={" ".join(arguments)}')

        if command == 'exit':
            break

        # Transform list of arg to a dict
        # from: ['xxx', 'yyy', ... ] -> to: {'xxx': 'yyy', ... }
        args = dict(zip_longest(*[iter(arguments)] * 2, fillvalue=""))
        if 'type' in args:
            database.store(
                'obs', {
                    'sequencer_command_received': args,
                    'sequencer_obs_type': args['type']
                })
        else:
            database.store('obs', {'sequencer_command_received': args})

        # try to cast every values of args dict in type needed
        check = cast_args(args)
        if check != 0:
            database.store('obs', {'sequencer_status': SequencerStatus.ERROR})
            logger.error('sequencer', 'Casting of args went wrong')
            continue

        # If abort command, start abort func and stop last command
        if 'ABORT' in command:
            database.store('obs',
                           {'sequencer_status': SequencerStatus.ABORTING})
            logger.info('sequencer', f'Received {command}. Aborting sequence.')

            commands.commands[command]()

            if th is not None:
                th.join()
                th = None

            database.store('obs',
                           {'sequencer_status': SequencerStatus.WAITING})
        else:
            if th is not None:
                th.join()
                th = None

            if 'alphacat' in args and 'deltacat' in args:
                coord = SkyCoord(ra=args['alphacat'], dec=args['deltacat'],
                                 unit=(u.hourangle, u.deg), frame='icrs')

                database.store('obs', {
                    'target_ra': coord.ra.deg,
                    'target_dec': coord.dec.deg
                })

                # Pre-configure ADCs
                zenith_angle = euler.telescope_future_zenith_angle(coord)
                adc.configure(zenith_angle=zenith_angle,
                              skip_tracking_check=True, blocking=False)

            database.store('obs', {'sequencer_status': SequencerStatus.SETUP})
            logger.info('sequencer', f'Starting {command}')

            th = Thread(target=execute_command, kwargs={
                'command': command,
                'seq_args': args
            })
            th.start()

    # in case of break, we disconnect the socket
    conn.close()
    socketSeq.close()
    database.store('obs', {'sequencer_status': SequencerStatus.OFF})
    logger.info('sequencer', 'Sequencer server off')

    return ReturnCode.SEQ_OK


def cast_args(args: dict[str, Any]) -> ReturnCode:
    """
    Modifies the dictionary received in parameter by trying to cast the values in the required type.
    The required types are stored in the configuration file.

    :param args: dict with keys: param name, values: param in
    :return: 0 if there was no error and 1 otherwise
    """

    # Check for each key if the cast of the value is possible and cast it
    for k, v in args.items():
        if k in config.SEQ.gop_arg_int:
            if v.isdigit():
                args[k] = int(v)
            else:
                logger.error('sequencer',
                             f'{k} value cannot be convert in int')
        elif k in config.SEQ.gop_arg_float:
            if v.replace('.', '', 1).isdigit():
                args[k] = float(v)
            else:
                logger.error('sequencer',
                             f'{k} value cannot be convert in float')
        elif k in config.SEQ.gop_arg_string:
            # If filterposition arg is not a digit, then he must be a name
            # Get the int id from the dict Id_filter
            # If filterposition arg is a digit, cast it in int
            if k == 'filterposition' and not v.isdigit():
                args[k] = filterwheel.translate_to_filter_position(v)
            elif k == 'filterposition' and v.isdigit():
                args[k] = int(v)
        # else:
        #     ignored_args[k] = v
        #     logger.error('sequencer', f'{k} not in arg list')
        #     return 1

        if k == 'kalfilter' and isinstance(v, str):
            args[k] = v.lower()

    return ReturnCode.SEQ_OK


def execute_command(command: str, seq_args: dict[str, Any]) -> ReturnCode:
    try:
        commands.commands[command](**seq_args)
    except AbortRequested:
        database.store('obs', {'sequencer_status': SequencerStatus.WAITING})
        logger.info('sequencer', f'{command} aborted on request')
        return ReturnCode.SEQ_OK
    except FLICancelFailed:
        database.store('obs', {'sequencer_status': SequencerStatus.WAITING})
        logger.info('sequencer', f'FLI cancel failed in {command}')
        return ReturnCode.SEQ_ERROR
    except SequencerException as e:
        database.store('obs', {'sequencer_status': SequencerStatus.ERROR})
        logger.error('sequencer', f'"{e.__doc__}" happened during {command}')

        # Close shutter after exception
        if shutter.close() != ShutterState.CLOSED:
            logger.error('sequencer',
                         'Failed to close the shutter after error')

        return ReturnCode.SEQ_ERROR
    except Exception as e:
        database.store('obs', {'sequencer_status': SequencerStatus.ERROR})
        logger.error('sequencer',
                     f'Unknown exception occurred during {command}')

        rprint(''.join(traceback.format_exception(e)))

        # Close shutter after exception
        if shutter.close() != ShutterState.CLOSED:
            logger.error('sequencer',
                         'Failed to close the shutter after error')

        return ReturnCode.SEQ_ERROR
    else:
        database.store('obs', {'sequencer_status': SequencerStatus.WAITING})
        logger.info('sequencer', f'{command} ended')

        return ReturnCode.SEQ_OK


if __name__ == '__main__':
    database.store('obs', {'sequencer_status': SequencerStatus.INITIALISING})

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    init()
    serve()
