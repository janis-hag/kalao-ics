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
from time import sleep
from itertools import zip_longest

from kalao.interface import info
from kalao.utils import database, kalao_time
from tcs_communication.pygop import tcs_srv_gop

from kalao_enums import TrackingStatus

import kalao_config as config

#sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
#sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__)))+os.path(pymod_libgop))
#sys.path.append('/home/kalao/kalao-ics/tcs_communication/pymod_libgop')

#TODO check if socket is available  and handle case when "Error: connection to sequencer refused" with retry and timeout


def gop_print_and_log(log_text):
    """
    Print out message to stdout and log message

    :param log_text: text to be printed and logged
    :return:
    """

    print(str(kalao_time.now()) + ' ' + log_text)
    database.store_obs_log({'gop_log': log_text})


def gop_server():
    """
    The main server code to run. It is listening on the IP and port defined in kalao.config

    :return:
    """

    # Initialise Gop (Geneva Observatory Protocol)
    gop = tcs_srv_gop.gop()

    gop.processesRegistration(config.GOP.ip)

    gop_print_and_log("Initialize new gop connection. Wait for client ...")
    # gc = gop.initializeGopConnection(socketName, verbosity)
    gc = gop.initializeInetGopConnection(config.GOP.ip, config.GOP.port,
                                         config.GOP.verbosity)
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
                gop_print_and_log(
                        "Initialize new gop connection. Wait for client ...")
                # gc = gop.initializeGopConnection(socketName, verbosity)
                gc = gop.initializeInetGopConnection(config.GOP.ip,
                                                     config.GOP.port,
                                                     config.GOP.verbosity)
                break
            elif controlRead[-1] == '#':
                command += controlRead[:-1]  # concat input string
            else:
                command += controlRead  # concat input string

        if controlRead == -1:
            continue  # go to beginning

        gop_print_and_log("After gop.read() := " + str(command))

        separator = command[0]
        command = command[1:]
        commandList = command.split(separator)
        #
        # 'command' is commandList[0], 'arguments' are commandList[1:]
        #
        #if len(commandList>1):
        #    gop_print_and_log(" command=> "+str(commandList[0])+" < arg="+commandList[1:].join(' '))
        gop_print_and_log(" command=> " + str(commandList[0]) + " < arg=" +
                          ' '.join(commandList[1:]))

        socket_connection_error = False

        # if commandList[0] == "STOPAO" or commandList[
        #         0] == "INSTRUMENTCHANGE" or commandList[0] == "NOTHING":
        #     # For the moment no difference is made for these three cases
        #     database.store_obs_log({'tracking_status': TrackingStatus.IDLE})
        #     commandList[0] = 'K_END'
        #     command = 'K_END'
        #     #gop.write("/OK")

        # Check if it's a KalAO command and send it
        if commandList[0][:1] == "K" or commandList[
                0] == "INSTRUMENTCHANGE" or commandList[
                        0] == "THE_END" or commandList[0] == "ABORT":

            hostSeq, portSeq = (config.SEQ.ip, config.SEQ.port)
            socketSeq = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                socketSeq.connect((hostSeq, portSeq))
                gop_print_and_log("Connected to sequencer")

                commandKal = separator + command
                socketSeq.sendall(commandKal.encode("utf8"))
                gop_print_and_log("Command sent")

            except ConnectionRefusedError:
                gop_print_and_log("Error: connection to sequencer refused")
                socket_connection_error = True
            finally:
                socketSeq.close()

        if socket_connection_error:
            sleep(10)
            continue

        if commandList[0] == "TEST":
            message = "/OK"
            #gop_print_and_log("Send acknowledge: " + str(message))
            gop.write(message)

        elif commandList[0] == "ONTARGET":
            message = "/OK"
            args = dict(zip_longest(*[iter(commandList[1:])] * 2,
                                    fillvalue=""))

            database.store_obs_log({
                    'tcs_header_path': args['header'],
                    'telescope_ra': float(args['ra']),
                    'telescope_dec': float(args['dec']),
                    'tracking_status': TrackingStatus.TRACKING
            })

            gop_print_and_log("Received fits header path: " +
                              str(commandList[1]))

            gop.write(message)

        # elif commandList[0] == "STOPAO" or commandList[
        #         0] == "INSTRUMENTCHANGE" or commandList[0] == "NOTHING":
        #     # TODO
        #     # Stop AO
        #     # Close shutter
        #     # reset_dms:
        #     aocontrol.reset_dm(config.AO.TTM_loop_number)
        #     # Set tracking to no-tracking keyword
        #     # Disable manual centering flag
        #     message = "/OK"
        #     database.store_obs_log({'tracking_status': TrackingStatus.IDLE})
        #     gop_print_and_log("Send acknowledge and quit: " + str(message))
        #     gop.write(message)
        #     #gop_print_and_log("Acknowledge sent")

        elif (commandList[0] == "quit") or (commandList[0] == "exit"):
            message = "/OK"
            gop_print_and_log("Send acknowledge and quit: " + str(message))
            gop.write(message)
            #gop_print_and_log("Acknowledge sent")
            break

        elif commandList[0] == "STATUS":
            message = info.kalao_status()
            gop_print_and_log("Send status: " + str(message))
            gop.write(message)

        else:
            message = "/OK"
            #gop_print_and_log("Send acknowledge: " + str(message))
            gop.write(message)
    #
    # in case of break, we disconnect all servers
    #

    gop_print_and_log(str(config.GOP.ip) + " close gop connection and exit")

    gop.closeConnection()
    #sys.exit(0)

    return 0


if __name__ == "__main__":
    gop_server()
