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

import socket
import time

from kalao import database, logger
from kalao.interfaces import edp

from tcs_communication.pygop import tcs_srv_gop

import config

#TODO check if socket is available  and handle case when "Error: connection to sequencer refused" with retry and timeout


def gop_server():
    """
    The main server code to run. It is listening on the IP and port defined in kalao.config

    :return:
    """

    # Initialise Gop (Geneva Observatory Protocol)
    gop = tcs_srv_gop.gop()

    gop.processesRegistration(config.GOP.ip)

    logger.info('gop', 'Initialize new gop connection. Wait for client ...')
    gc = gop.initializeInetGopConnection(config.GOP.ip, config.GOP.port,
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
                gc = gop.initializeInetGopConnection(config.GOP.ip,
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

        logger.info('gop', f'command=> {command} < arg={" ".join(arguments)}')

        # Check if it's a KalAO command and send it
        if command.startswith('K_') or command in [
                'INSTRUMENTCHANGE', 'THE_END', 'ABORT', 'STOPAO'
        ]:
            if command in ['INSTRUMENTCHANGE', 'THE_END', 'STOPAO']:
                database.store('obs', {'sequencer_on_target': False})

            hostSeq, portSeq = (config.SEQ.ip, config.SEQ.port)
            socketSeq = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                socketSeq.connect((hostSeq, portSeq))
                logger.info('gop', 'Connected to sequencer')

                socketSeq.sendall(commandRaw.encode('utf8'))
                logger.info('gop', 'Command sent')

            except ConnectionRefusedError:
                logger.error('gop', 'Connection to sequencer refused')
                time.sleep(10)
                continue
            finally:
                socketSeq.close()

            message = "/OK"
            logger.info('gop', f'Sending acknowledge: {message}')
            gop.write(message)

        elif command == 'TEST':
            message = '/OK'
            logger.info('gop', f'Sending acknowledge: {message}')
            gop.write(message)

        elif command == 'ONTARGET':
            message = '/OK'

            database.store('obs', {
                'tcs_header_path': arguments[0],
            })

            database.store('obs', {'sequencer_on_target': True})

            logger.info('gop', f'Received fits header path: {arguments[0]}')

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
    logger.info('gop', f'{config.GOP.ip} close gop connection and exit')

    gop.closeConnection()

    return 0


if __name__ == "__main__":
    gop_server()
