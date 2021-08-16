#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sys import path as SysPath
from os  import path as OsPath
# methode dirname return parent directory and methode abspath return absolut path
SysPath.append(OsPath.dirname(OsPath.abspath(OsPath.dirname(__file__))))

from sequencer import seq_command

from kalao.utils import database
from kalao.filterwheel import control

import socket
import time

from itertools      import zip_longest
from configparser   import ConfigParser
from queue          import Queue
from threading      import Thread


# Read config file
parser = ConfigParser()
config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
parser.read(config_path)

def seq_server():
    """
    receive commands in string form through a socket.
    format them into a dictionary.
    create a thread to execute the command.

    :return:
    """

    host = parser.get('SEQ','IP')
    port = parser.get('SEQ','Port')

    # check if config value format is right
    if port.isdigit():
        port = int(port)
    else:
        print("Error: wrong values format for 'Port' in kalao.config file ")
        return

    socketSeq = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketSeq.bind((host, port))
    print("%.6f"%(time.time()), "Server on")

    q = Queue()
    th = None
    preCommand = ""

    while True:
        socketSeq.listen()
        print("%.6f"%(time.time()), "Waiting on connection..")
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
        print("%.6f"%(time.time()), " command=>", commandList[0], "< arg=",commandList[1:], sep="")

        if commandList[0] == 'exit':
            break

        # Transform list of arg to a dict and add Queue Object q
        # from: ['xxx', 'yyy', ... ] -> to: {'xxx': 'yyy', ... }
        args = dict(zip_longest(*[iter(commandList[1:])] * 2, fillvalue=""))
        args["q"] = q

        # try to cast every values of args dict in type needed
        check = cast_args(args)
        if check != 0:
            print(check)
            database.store_obs_log({'sequencer_status': 'ERROR'})
            continue

        # if abort commande, stop last command with Queue object q
        # and start abort func
        if(commandList[0] == preCommand + '_abort'):
            q.put(1)
            seq_command.commandDict[commandList[0]](args)
            th.join()
            while not q.empty():
                q.get()
            database.store_obs_log({'sequencer_status': 'WAITING'})
            continue
        elif(th != None):
            th.join()

        # Start a subThread with received command
        # commandDict is a dict with keys = "kal_****" and values is function object
        th = Thread(target = seq_command.commandDict[commandList[0]], kwargs = args)
        th.start()

        preCommand = commandList[0]

    # in case of break, we disconnect the socket
    conn.close()
    socketSeq.close()
    print("%.6f"%(time.time()), 'Seq server off')


def cast_args(args):
    """
    Modifies the dictionary received in parameter by trying to cast the values in the required type.
    The required types are stored in the configuration file.

    :param args: dict with keys: param name, values: param in
    :return: 0 if there was no error and 1 otherwise
    """

    parser = ConfigParser()
    config_path = os.path.join(Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
    parser.read(config_path)

    # Create bidirect dict with filter id (str and int)
    Id_filter = control.create_filter_id()

    # Create a list from a string
    # from: "xxx, yyy, zzz" -> to: ['xxx', 'yyy', 'zzz']
    arg_int    = parser.get('SEQ','gop_arg_int').replace(' ', '').split(',')
    arg_float  = parser.get('SEQ','gop_arg_float').replace(' ', '').split(',')
    arg_string = parser.get('SEQ','gop_arg_string').replace(' ', '').split(',')

    # Check for each keys if the cast of the value is possible and cast it
    for k, v in args.items():
        if k in arg_int:
            if v.isdigit():
                args[k] = int(v)
            else:
                database.store_obs_log({'sequencer_log': "Error: {} value cannot be convert in int".format(k)})
                return 1
        elif k in arg_float:
            if v.replace('.', '', 1).isdigit():
                args[k] = float(v)
            else:
                database.store_obs_log({'sequencer_log': "Error: {} value cannot be convert in float".format(k)})
                return 1
        elif k in arg_string:
            # If filterposition arg is not a digit, then he must be a name
            # Get the int id from the dict Id_filter
            # If filterposition arg is a digit, cast it in int
            if k == 'filterposition' and not v.isdigit():
                args[k] = int(Id_filter[v])
            elif k == 'filterposition' and v.isdigit():
                args[k] = int(v)
        else:
            database.store_obs_log({'sequencer_log': "Error: {} not in arg list".format(k)})
            return 1

    return 0

if __name__ == "__main__":
    seq_server()
