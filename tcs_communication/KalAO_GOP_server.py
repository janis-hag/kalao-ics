#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : KalAO_GOP_server.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
KalAO_GOP_server.py is part of the KalAO Instrument Control Software
(KalAO-ICS).

This server is the communication interface between the Euler telescope software and the KalAO sequencer.
"""

from itertools import zip_longest
from typing import Any

import requests

from tcs_communication.pygop import tcs_srv_gop

from kalao import logger
from kalao.interfaces import edp

from kalao.definitions.enums import ReturnCode

import config


def gop_server():
    """
    The main server code to run. It is listening on the IP and port defined in kalao.config

    :return:
    """

    # Initialise Gop (Geneva Observatory Protocol)
    gop = tcs_srv_gop.gop()

    gop.processesRegistration(config.GOP.host)

    logger.info('gop', 'Initialize new gop connection. Wait for client ...')
    gc = gop.initializeInetGopConnection(config.GOP.host, config.GOP.port,
                                         config.GOP.verbosity)
    #
    # Infinite loop, waiting for command
    # Rem; all command reply an acknowledgement
    #
    while True:
        logger.info('gop', 'Wait for command')
        #
        # read and concat until "#" char, then parse the input string
        #
        commandRaw = ""
        controlRead = "#"
        while '#' in controlRead:
            #  '#' signe used to signify end of command
            controlRead = gop.read()

            if controlRead == -1:
                gc = gop.closeConnection()
                logger.info(
                    'gop',
                    'Initialize new gop connection. Wait for client ...')
                # gc = gop.initializeGopConnection(socketName, verbosity)
                gc = gop.initializeInetGopConnection(config.GOP.host,
                                                     config.GOP.port,
                                                     config.GOP.verbosity)
                break
            elif controlRead[-1] == '#':
                commandRaw += controlRead[:-1]  # concat input string
            else:
                commandRaw += controlRead  # concat input string

        if controlRead == -1:
            continue  # go to beginning

        logger.info('gop', f'After gop.read() := {commandRaw}')

        separator = commandRaw[0]
        commandList = commandRaw[1:].split(separator)

        command = commandList[0]
        arguments = commandList[1:]

        arguments = dict(zip_longest(*[iter(arguments)] * 2, fillvalue=""))

        cast_args(arguments)

        logger.info('gop', f'command=> {command} < arg={" ".join(arguments)}')

        # Check if it's a KalAO command and send it
        if 'ABORT' in command:
            ret, _ = _send_request('POST', '/abort', {})

            if ret == ReturnCode.OK:
                message = "/OK"
            else:
                message = "/ERROR"

            logger.info('gop', f'Sending acknowledge: {message}')
            gop.write(message)

        elif command.startswith('K_') or command in [
                'INSTRUMENTCHANGE', 'THE_END', 'OBCHANGE'
        ]:
            ret, _ = _send_request(
                'POST', f'/template/{command.replace("K_", "KAO_")}',
                arguments)

            if ret == ReturnCode.OK:
                message = "/OK"
            else:
                message = "/ERROR"

            logger.info('gop', f'Sending acknowledge: {message}')
            gop.write(message)

        elif command == 'TEST':
            message = '/OK'
            logger.info('gop', f'Sending acknowledge: {message}')
            gop.write(message)

        elif command == 'ONTARGET':
            logger.info(
                'gop',
                f'Received fits header path: {list(arguments.keys())[0]}')

            ret, _ = _send_request('POST', f'/on_target', {
                'tcs_header_path': list(arguments.keys())[0]
            })

            if ret == ReturnCode.OK:
                message = "/OK"
            else:
                message = "/ERROR"

            logger.info('gop', f'Sending acknowledge: {message}')
            gop.write(message)

        elif command == 'quit' or command == 'exit':
            message = '/OK'
            logger.info('gop', f'Sending acknowledge and quit: {message}')
            gop.write(message)
            break

        elif command == 'STATUS':
            message = edp.kalao_status()
            logger.info('gop', f'Sending status: {message}')
            gop.write(message)

        else:
            message = "/OK"
            logger.info('gop', f'Sending acknowledge: {message}')
            gop.write(message)

    # in case of break, we disconnect all servers
    logger.info('gop', f'{config.GOP.host} close gop connection and exit')

    gop.closeConnection()

    return 0


def cast_args(args: dict[str, Any]) -> int:
    """
    Modifies the dictionary received in parameter by trying to cast the values in the required type.
    The required types are stored in the configuration file.

    :param args: dict with keys: param name, values: param in
    :return: 0 if there was no error and 1 otherwise
    """

    # Check for each key if the cast of the value is possible and cast it
    for k, v in args.items():
        if k in config.GOP.arg_int:
            if v.isdigit():
                args[k] = int(v)
            else:
                logger.error('gop', f'{k} value cannot be convert in int')
        elif k in config.GOP.arg_float:
            if v.replace('.', '', 1).isdigit():
                args[k] = float(v)
            else:
                logger.error('gop', f'{k} value cannot be convert in float')

        if k == 'kalfilter' and isinstance(v, str):
            v = v.lower()
            if v in ['g', 'r', 'i', 'z']:
                args[k] = 'SDSS-' + v
            elif v == 'nd':
                args[k] = 'ND1.5'

        elif k == 'kao':
            args[k] = v.upper()

    return 0


def _send_request(method: str, endpoint: str, params: dict[str, Any] |
                  None = None) -> tuple[ReturnCode, Any]:
    kwargs = {}
    if method == 'POST' and params is not None:
        kwargs['json'] = params

    try:
        req = requests.request(
            method, f'http://127.0.0.1:{config.Sequencer.port}{endpoint}',
            timeout=config.Camera.request_timeout, **kwargs)

        req.raise_for_status()

        if req.headers.get('content-type', '').startswith('application/json'):
            return ReturnCode.OK, req.json()
        else:
            return ReturnCode.OK, req.text

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return ReturnCode.GENERIC_ERROR, None

    except requests.exceptions.HTTPError:
        logger.error(
            'gop',
            f'Sequencer server endpoint {endpoint} answered with an Error {req.status_code}, {req.text}'
        )
        return ReturnCode.GENERIC_ERROR, None


if __name__ == '__main__':
    gop_server()
