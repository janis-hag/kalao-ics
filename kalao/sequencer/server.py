#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
import socket
import time
import traceback
from itertools import zip_longest
from multiprocessing import Process, Queue
from threading import Thread

from astropy import units as u
from astropy.coordinates import SkyCoord

from kalao import database, euler, logger, services
from kalao.plc import (adc, calibunit, filterwheel, flipmirror, laser, shutter,
                       tungsten)
from kalao.sequencer import commands

from kalao.definitions.enums import ReturnCode, SequencerStatus, ShutterState
from kalao.definitions.exceptions import *

import config

conn = None
socketSeq = None


def handler(signal_received, frame):
    if signal_received == signal.SIGINT or signal_received == signal.SIGTERM:
        print('\nSIGTERM or SIGINT or CTRL-C detected. Exiting.')

        if conn is not None:
            conn.close()

        if socketSeq is not None:
            socketSeq.close()

        database.store('obs', {'sequencer_status': SequencerStatus.OFF})
        logger.info('sequencer', 'Sequencer server off')

        exit(0)


def init():
    init_list = [
        services.init,
        calibunit.init,
        flipmirror.init,
        shutter.init,
        tungsten.init,
        laser.init,
        filterwheel.init,
        lambda: adc.init(config.PLC.Node.ADC1),
        lambda: adc.init(config.PLC.Node.ADC2),
    ]

    def get_name(f):
        return f'{f.__module__}.{f.__name__}'

    def wrapper(f, q):
        ret = f()
        q.put({get_name(f): ret})

    processes = {}
    processes_terminated = {}
    processes_killed = {}
    processes_error = {}
    return_queue = Queue()
    time_start = time.monotonic()

    # Launch all processes
    for f in init_list:
        p = Process(target=wrapper, kwargs={'f': f, 'q': return_queue})
        processes[get_name(f)] = p
        p.start()

    # Wait for all processes to finish
    for p in processes.values():
        p.join(config.SEQ.init_timeout - (time.monotonic() - time_start))

    # Terminate remaining ones
    for f, p in processes.items():
        if p.is_alive():
            logger.warn('sequencer', f'Terminating process for {f}')
            processes_terminated[f] = p

            p.terminate()

    if processes_terminated != 0:
        time.sleep(config.SEQ.init_terminate_grace_time)

    # Kill them if necessary
    for f, p in processes.items():
        if p.is_alive():
            logger.warn('sequencer', f'Killing process for {f}')
            processes_killed[f] = p

            p.kill()

    if processes_killed != 0:
        time.sleep(config.SEQ.init_wait_kill)

    time_stop = time.monotonic()

    # Collecting return values of processes that finished
    returns = {}
    while not return_queue.empty():
        returns.update(return_queue.get_nowait())

    for f, ret in returns.items():
        if ret != ReturnCode.OK:
            logger.error('sequencer',
                         f'Initialisation failed for {f}, returned {ret}')
            processes_error[f] = ret

    logger.info(
        'sequencer',
        f'Initialisation finished in {time_stop - time_start:.1f}s. {len(processes)} launched, {len(processes_terminated)} terminated, {len(processes_killed)} killed, {len(processes_error)} returned with error'
    )

    return 0


def serve():
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

        commandRaw = (conn.recv(4096)).decode("utf8")

        separator = commandRaw[0]
        commandList = commandRaw[1:].split(separator)

        command = commandList[0]
        arguments = commandList[1:]

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


def cast_args(args):
    """
    Modifies the dictionary received in parameter by trying to cast the values in the required type.
    The required types are stored in the configuration file.

    :param args: dict with keys: param name, values: param in
    :return: 0 if there was no error and 1 otherwise
    """

    # Translate keyword if not already present
    for edp_arg, kalao_arg in config.SEQ.EDP_translate.items():
        if edp_arg in args and kalao_arg not in args:
            args[kalao_arg] = args.pop(edp_arg)

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
                args[k] = filterwheel.translate_to_filter_position(filter)
            elif k == 'filterposition' and v.isdigit():
                args[k] = int(v)
        # else:
        #     ignored_args[k] = v
        #     logger.error('sequencer', f'{k} not in arg list')
        #     return 1

        if k == 'kalfilter' and isinstance(v, str):
            args[k] = v.lower()

    return 0


def execute_command(command, seq_args):
    try:
        commands.commands[command](**seq_args)
    except AbortRequested:
        database.store('obs', {'sequencer_status': SequencerStatus.WAITING})
        logger.info('sequencer', f'{command} aborted on request')
    except FLICancelFailed:
        database.store('obs', {'sequencer_status': SequencerStatus.WAITING})
        logger.info('sequencer', f'FLI cancel failed in {command}')
    except SequencerException as e:
        database.store('obs', {'sequencer_status': SequencerStatus.ERROR})
        logger.error('sequencer', f'"{e.__doc__}" happened during {command}')

        # Close shutter after exception
        if shutter.close() != ShutterState.CLOSED:
            logger.error('sequencer',
                         'Failed to close the shutter after error')
    except Exception as e:
        database.store('obs', {'sequencer_status': SequencerStatus.ERROR})
        logger.error('sequencer',
                     f'Unknown exception occured during {command}')

        traceback.print_exc()

        # Close shutter after exception
        if shutter.close() != ShutterState.CLOSED:
            logger.error('sequencer',
                         'Failed to close the shutter after error')
    else:
        database.store('obs', {'sequencer_status': SequencerStatus.WAITING})
        logger.info('sequencer', f'{command} ended')


if __name__ == "__main__":
    database.store('obs', {'sequencer_status': SequencerStatus.INITIALISING})
    logger.info('sequencer', 'Server initialisation')

    if init() != 0:
        logger.error('sequencer', 'Initialisation failed')

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    serve()
