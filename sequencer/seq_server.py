#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#from signal import SIGINT, SIGTERM
import signal
from sys import path as SysPath
from os  import path as OsPath
# methode dirname return parent directory and methode abspath return absolut path
SysPath.append(OsPath.dirname(OsPath.abspath(OsPath.dirname(__file__))))

from pathlib import Path

from sequencer import seq_command, system

from kalao.utils import database, kalao_time
from kalao.plc import filterwheel

import socket
#import time
import os

from itertools      import zip_longest
from configparser   import ConfigParser
from queue          import Queue
from threading      import Thread

#TODO clean config reading and loading procedure

config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
if os.access(config_path, os.R_OK):
    # Read config file
    parser = ConfigParser()
    parser.read(config_path)
else:
    system.print_and_log('kalao.config not found on path: '+str(config_path))
    sys.exit(1)

def seq_server():
    """
    receive commands in string form through a socket.
    format them into a dictionary.
    create a thread to execute the command.

    :return:
    """

    host = parser.get('SEQ','IP')
    port = parser.getint('SEQ','Port')

    socketSeq = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketSeq.bind((host, port))
    system.print_and_log("Server on: "+str(kalao_time.now()))

    conn = None

    def handler(signal_received, frame):
        # Handle any cleanup here
        if signal_received == signal.SIGTERM:
            # Restarting using systemd framework
            print('\nSIGTERM received. Restarting.')
            if conn is not None:
                conn.close()
            socketSeq.close()
            system.print_and_log("Sequencer server off: " + str(kalao_time.now()))
            #system.se_Server_service('RESTART')
        elif signal_received == signal.SIGINT:
            print('\nSIGINT or CTRL-C detected. Exiting.')
            if conn is not None:
                conn.close()
            socketSeq.close()
            system.print_and_log("Sequencer server off: " + str(kalao_time.now()))
            exit(0)

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    q = Queue()
    th = None
    preCommand = ""

    while True:
        socketSeq.listen()
        database.store_obs_log({'sequencer_log': "Waiting on connection."})
        conn, address = socketSeq.accept()

        command = (conn.recv(4096)).decode("utf8")
        database.store_obs_log({'sequencer_status': 'BUSY'})
        # store BUSY when a command is received

        separator   = command[0]
        command     = command[1:]
        commandList = command.split(separator)
        #
        # 'command' is commandList[0], 'arguments' are commandList[1:]
        #
        print("%s"%(kalao_time.now()), " command=>", commandList[0], "< arg=",commandList[1:], sep="")

        if commandList[0] == 'exit':
            break

        # Transform list of arg to a dict and add Queue Object q
        # from: ['xxx', 'yyy', ... ] -> to: {'xxx': 'yyy', ... }
        args = dict(zip_longest(*[iter(commandList[1:])] * 2, fillvalue=""))
        args["q"] = q

        # try to cast every values of args dict in type needed
        check = cast_args(args)
        if check != 0:
            print("Error: casting of args went wrong")
            database.store_obs_log({'sequencer_status': 'ERROR'})
            continue

        # if abort command, stop last command with Queue object q
        # and start abort func
        if(commandList[0] == preCommand + '_ABORT'):
            # adds 1 to the q object to communicate the abort instruction
            q.put(1)
            seq_command.commandDict[commandList[0]]()
            th.join()
            while not q.empty():
                q.get()
            database.store_obs_log({'sequencer_status': 'WAITING'})
            continue
        # if not abort, but a thread exist, wait for the thread end
        elif(th != None):
            th.join()

        # Start a subThread with received command
        # commandDict is a dict with keys = "K_****" and values is function object
        # it may need to be kwargs = **args as we are passing a dictionary
        th = Thread(target=seq_command.commandDict[commandList[0]], kwargs = args)
        th.start()

        preCommand = commandList[0]

    # in case of break, we disconnect the socket
    conn.close()
    socketSeq.close()
    system.print_and_log("Sequencer server off: "+str(kalao_time.now()))


def cast_args(args):
    """
    Modifies the dictionary received in parameter by trying to cast the values in the required type.
    The required types are stored in the configuration file.

    :param args: dict with keys: param name, values: param in
    :return: 0 if there was no error and 1 otherwise
    """

    parser = ConfigParser()
    config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
    parser.read(config_path)

    # Create bidirect dict with filter id (str and int)
    Id_filter = filterwheel.create_filter_id()

    # Create a list from a string
    # from: "xxx, yyy, zzz" -> to: ['xxx', 'yyy', 'zzz']
    arg_int    = parser.get('SEQ','gop_arg_int').replace(' ', '').split(',')
    arg_float  = parser.get('SEQ','gop_arg_float').replace(' ', '').split(',')
    arg_string = parser.get('SEQ','gop_arg_string').replace(' ', '').split(',')

    # Create dictionary to translate EDP argument to KalAO arguments
    edp_translation_dict = {}
    for key, val in parser.items('EDP_translate'):
        edp_translation_dict[key] = val

    # Translate keyword if not already present
    for edp_arg, kalao_arg in edp_translation_dict.items():
        if edp_arg in args.keys() and not kalao_arg in args.keys():
            args[kalao_arg] = args.pop(edp_arg)

    # Check for each keys if the cast of the value is possible and cast it
    for k, v in args.items():
        if k in arg_int:
            if v.isdigit():
                args[k] = int(v)
            else:
                database.store_obs_log({'sequencer_log': "Error: {} value cannot be convert in int".format(k)})
        elif k in arg_float:
            if v.replace('.', '', 1).isdigit():
                args[k] = float(v)
            else:
                database.store_obs_log({'sequencer_log': "Error: {} value cannot be convert in float".format(k)})
        elif k in arg_string:
            # If filterposition arg is not a digit, then he must be a name
            # Get the int id from the dict Id_filter
            # If filterposition arg is a digit, cast it in int
            if k == 'filterposition' and not v.isdigit():
                args[k] = int(Id_filter[v])
            elif k == 'filterposition' and v.isdigit():
                args[k] = int(v)
        # else:
        #     ignored_args[k] = v
        #     database.store_obs_log({'sequencer_log': "Error: {} not in arg list".format(k)})
        #     return 1

    return 0

if __name__ == "__main__":
    seq_server()
