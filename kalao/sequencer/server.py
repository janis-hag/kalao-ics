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

from kalao import services
from kalao.plc import (adc, calib_unit, filterwheel, flip_mirror, laser,
                       shutter, tungsten)
from kalao.sequencer import commands
from kalao.utils import database

from kalao.definitions.enums import ReturnCode, SequencerStatus
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

        database.store(
            'obs', {
                'sequencer_log': f'Sequencer server off',
                'sequencer_status': SequencerStatus.OFF
            })

        exit(0)


def init():
    init_list = [
        services.init,
        calib_unit.init,
        flip_mirror.init,
        shutter.init,
        tungsten.init,
        laser.init,
        lambda: adc.init(1),
        lambda: adc.init(2),
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
            database.store('obs', {
                'sequencer_log': f'[WARNING] Terminating process for {f}'
            })
            processes_terminated[f] = p

            p.terminate()

    if processes_terminated != 0:
        time.sleep(config.SEQ.init_terminate_grace_time)

    # Kill them if necessary
    for f, p in processes.items():
        if p.is_alive():
            database.store('obs', {
                'sequencer_log': f'[WARNING] Killing process for {f}'
            })
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
        if ret != ReturnCode.NOERROR:
            database.store(
                'obs', {
                    'sequencer_log':
                        f'[ERROR] Initialisation failed for {f}, returned {ret}'
                })
            processes_error[f] = p

    database.store(
        'obs', {
            'sequencer_log':
                f'Initialisation finished in {time_stop - time_start}s. {len(processes)} launched, {len(processes_terminated)} terminated, {len(processes_error)} returned with error'
        })

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

    q = Queue()
    th = None

    database.store('obs', {
        'sequencer_log': f'Server on',
        'sequencer_status': SequencerStatus.WAITING
    })

    while True:
        socketSeq.listen()
        database.store('obs', {'sequencer_log': 'Waiting on connection'}
                       # Do NOT update sequencer_status
                       )

        conn, address = socketSeq.accept()

        commandRaw = (conn.recv(4096)).decode("utf8")

        separator = commandRaw[0]
        commandList = commandRaw[1:].split(separator)

        command = commandList[0]
        arguments = commandList[1:]

        database.store(
            'obs', {
                'sequencer_log':
                    f'command=> {command} < arg={" ".join(arguments)}',
                'sequencer_status':
                    SequencerStatus.BUSY
            })

        if command == 'exit':
            break

        # Transform list of arg to a dict and add Queue Object q
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

        args["q"] = q

        # try to cast every values of args dict in type needed
        check = cast_args(args)
        if check != 0:
            database.store(
                'obs', {
                    'sequencer_log': '[ERROR] Casting of args went wrong',
                    'sequencer_status': SequencerStatus.ERROR
                })
            continue

        # if abort command, stop last command with Queue object q
        # and start abort func
        if 'ABORT' in command:
            database.store(
                'obs', {
                    'sequencer_log': f'Received {command}. Aborting sequence.',
                    'sequencer_status': SequencerStatus.ABORTING
                })

            q.put('abort')
            commands.commands[command]()
            th.join()

            while not q.empty():
                q.get()

            database.store('obs',
                           {'sequencer_status': SequencerStatus.WAITING})
        else:
            if th is not None:
                th.join()
                th = None

            if 'alphacat' in args and 'deltacat' in args:

                c = SkyCoord(ra=args['alphacat'], dec=args['deltacat'],
                             unit=(u.hourangle, u.deg), frame='icrs')

                database.store('obs', {
                    'telescope_ra': c.ra.deg,
                    'telescope_dec': c.dec.deg
                })

            database.store(
                'obs', {
                    'sequencer_log': f'Starting {command}',
                    'sequencer_status': SequencerStatus.SETUP
                })

            th = Thread(target=execute_command, kwargs={
                'command': command,
                'seq_args': args
            })
            th.start()

    # in case of break, we disconnect the socket
    conn.close()
    socketSeq.close()
    database.store(
        'obs', {
            'sequencer_log': f'Sequencer server off',
            'sequencer_status': SequencerStatus.OFF
        })


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
                database.store('obs', {
                    'sequencer_log':
                        f'[ERROR] {k} value cannot be convert in int'
                })
        elif k in config.SEQ.gop_arg_float:
            if v.replace('.', '', 1).isdigit():
                args[k] = float(v)
            else:
                database.store(
                    'obs', {
                        'sequencer_log':
                            f'[ERROR] {k} value cannot be convert in float'
                    })
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
        #     database.store('obs',{'sequencer_log': f'[ERROR] {k} not in arg list'})
        #     return 1

    return 0


def execute_command(command, seq_args):
    try:
        commands.commands[command](**seq_args)
    except AbortRequested:
        database.store(
            'obs', {
                'sequencer_log': f'{command} aborted on request',
                'sequencer_status': SequencerStatus.WAITING
            })
    except FLICancelFailed:
        database.store(
            'obs', {
                'sequencer_log': f'FLI cancel failed in {command}',
                'sequencer_status': SequencerStatus.WAITING
            })
    except SequencerException as e:
        database.store(
            'obs', {
                'sequencer_log':
                    f'[ERROR] "{e.__doc__}" happened during {command}',
                'sequencer_status':
                    SequencerStatus.ERROR
            })
    except Exception as e:
        database.store(
            'obs', {
                'sequencer_log':
                    f'[ERROR] Unknown exception occured during {command}',
                'sequencer_status':
                    SequencerStatus.ERROR
            })

        traceback.print_exc()
    else:
        database.store(
            'obs', {
                'sequencer_log': f'{command} ended',
                'sequencer_status': SequencerStatus.WAITING
            })


if __name__ == "__main__":
    database.store(
        'obs', {
            'sequencer_log': 'Server initialisation',
            'sequencer_status': SequencerStatus.INITIALISING
        })

    if init() != 0:
        database.store('obs',
                       {'sequencer_log': '[ERROR] Initialisation failed'})

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    serve()
