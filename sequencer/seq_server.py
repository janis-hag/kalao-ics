#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sys import path as SysPath
from os  import path as OsPath
# methode dirname return parent directory and methode abspath return absolut path
SysPath.append(OsPath.dirname(OsPath.abspath(OsPath.dirname(__file__))))

from sequencer import seq_command

from kalao.utils import database

import socket
import time

from itertools      import zip_longest
from configparser   import ConfigParser
from queue          import Queue
from threading      import Thread

def seq_server():

    # Read config file and create a dict for each section where keys is parameter
    parser = ConfigParser()
    parser.read('../kalao.config')

    host = parser.get('SEQ','IP')
    port = parser.get('SEQ','Port')

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
        database.store_obs_log({'sequencer_status': 'busy'})

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
        args = dict(zip_longest(*[iter(commandList[1:])] * 2, fillvalue=""))
        args["q"] = q

        check = cast_args(args)
        if check != 0:
            print(check)
            database.store_obs_log({'sequencer_status': 'waiting'})
            continue
        # if abort commande, stop last command with Queue object q
        # and start abort func
        if(commandList[0] == preCommand + '_abort'):
            q.put(1)
            seq_command.commandDict[commandList[0]]()
            th.join()
            while not q.empty():
                q.get()
            database.store_obs_log({'sequencer_status': 'waiting'})
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

    # Read it from config file ?
    arg_int    = []
    arg_float  = ['dit', 'intensity']
    arg_string = ['filepath']

    for k, v in args:
        if k in arg_int:
            if v.isdigit():
                args[k] = int(v)
            else:
                return "Error: {} value cannot be convert in int".format(k)
        elif k in arg_float:
            if v.replace('.', '', 1).isdigit():
                args[k] = float(v)
            else:
                return "Error: {} value cannot be convert in float".format(k)
        elif k in arg_string:
            pass
        else:
            return "Error: {} not in arg list".format(k)

        return 0

if __name__ == "__main__":
    seq_server()
