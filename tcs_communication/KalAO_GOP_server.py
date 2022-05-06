#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : database_updater.py
# @Date : 2021-03-15-10-29
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
KalAO_GOP_server.py is part of the KalAO Instrument Control Software
(KalAO-ICS).

This server is the communication interface between the Euler telescope software and the KalAO sequencer.
"""

import os
import sys
import socket
from pathlib import Path
from configparser import ConfigParser

from kalao.interface import status
from kalao.utils import database, kalao_time
from tcs_communication.pygop import tcs_srv_gop

# Read config file
parser = ConfigParser()
config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
parser.read(config_path)

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
#sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__)))+os.path(pymod_libgop))
sys.path.append('/home/kalao/kalao-ics/tcs_communication/pymod_libgop')

#TODO check if socket is available  and handle case when "Error: connection to sequencer refused" with retry and timeout


def gop_print_and_log(log_text):
    '''
    Print out message to stdout and log message

    :param log_text: text to be printed and logged
    :return:
    '''
    print(str(kalao_time.now())+' '+log_text)
    database.store_obs_log({'gop_log': log_text})


def gop_server():
    # Initialise Gop (Geneva Observatory Protocol)
    gop = tcs_srv_gop.gop()

    socketName = parser.get('GOP', 'IP')
    socketPort = parser.getint('GOP', 'Port')  # only for inet connection

    sequencer_host = parser.get('SEQ', 'IP')
    sequencer_port = parser.getint('SEQ', 'Port')

    #
    verbosity = parser.getint('GOP', 'Verbosity')
    gop.processesRegistration(socketName)

    gop_print_and_log("Initialize new gop connection. Wait for client ...")
    # gc = gop.initializeGopConnection(socketName, verbosity)
    gc = gop.initializeInetGopConnection(socketName, socketPort, verbosity)
    #
    # Infinite loop, waiting for command
    # Rem; all command reply an acknowledgement
    #
    while True:
        print("")
        gop_print_and_log("Wait for command")
        #
        # read and concat until "#" char, then parse the input string
        #
        command = ""
        controlRead = "#"
        while '#' in controlRead:
            #  '#' signe used to signify end of command
            controlRead = gop.read()

            if controlRead == -1:
                gc = gop.closeConnection()
                gop_print_and_log("Initialize new gop connection. Wait for client ...")
                # gc = gop.initializeGopConnection(socketName, verbosity)
                gc = gop.initializeInetGopConnection(socketName, socketPort, verbosity)
                break
            elif  controlRead[-1] == '#':
                command += controlRead[:-1]  # concat input string
            else:
                command += controlRead  # concat input string

        if controlRead == -1:
            continue  # go to beginning

        gop_print_and_log("After gop.read() := "+str(command))

        separator = command[0]
        command = command[1:]
        commandList = command.split(separator)
        #
        # 'command' is commandList[0], 'arguments' are commandList[1:]
        #
        #if len(commandList>1):
        #    gop_print_and_log(" command=> "+str(commandList[0])+" < arg="+commandList[1:].join(' '))
        gop_print_and_log(" command=> " + str(commandList[0]) + " < arg=" + ' '.join(commandList[1:]))

        # Check if its a KalAO command and send it
        if commandList[0][:1] == "K":

            commandList[0] = commandList[0][2:].lower()

            hostSeq, portSeq = (sequencer_host, sequencer_port)
            socketSeq = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                socketSeq.connect((hostSeq, portSeq))
                gop_print_and_log("Connected to sequencer")

                commandKal = separator + command
                socketSeq.sendall(commandKal.encode("utf8"))
                gop_print_and_log("Command sent")

            except ConnectionRefusedError:
                gop_print_and_log("Error: connection to sequencer refused")
            finally:
                socketSeq.close()

        #
        # Manage the command. 2 cases:
        # - its a state machine (with a nodeId which starts with "ns=")
        # - its a local command (test, exit, ...)
        #

        if commandList[0] == "test":
            message = "/OK"
            gop_print_and_log("Send acknowledge: "+str(message))
            gop.write(message)
        elif (commandList[0] == "quit") or (commandList[0] == "exit"):
            message = "/OK"
            gop_print_and_log("Send acknowledge and quit: "+str(message))
            gop.write(message)
            gop_print_and_log("Acknowledge sent")
            break
        elif commandList[0] == "status":
            message = status.kalao_status()
            gop_print_and_log("Send status: "+str(message))
            gop.write(message)
        else:
            message = "/OK"
            gop_print_and_log("Send acknowledge: "+str(message))
            gop.write(message)
    #
    # in case of break, we disconnect all servers
    #

    gop_print_and_log(str(socketName)+" close gop connection and exit")

    gop.closeConnection()
    #sys.exit(0)

    return 0

if __name__ == "__main__":
    gop_server()
