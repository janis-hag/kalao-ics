#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import seq_command
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

    host = parser.get('PLC','IP')
    port = parser.getint('PLC','Port')

    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.bind((host, port))
    print("%.6f"%(time.time()), "Server on")

    q = Queue()
    th = None
    preCommand = ""

    while True:
        socket.listen()
        print("%.6f"%(time.time()), "Waiting on connection..")
        conn, address = socket.accept()

        command = (conn.recv(4096)).decode("utf8")

        separator   = command[0]
        command     = command[1:]
        commandList = command.split(separator)
        #
        # 'command' is commandList[0], 'arguments' are commandList[1:]
        #
        print("%.6f"%(time.time()), " command=>", commandList[0], "< arg=",commandList[1:], sep="")

        # Transform list of arg to a dict and add Queue Object q
        args = dict(zip_longest(*[iter(commandList[1:])] * 2, fillvalue=""))
        args["q"] = q

        # if abort commande, stop last command with Queue object q
        # and start abort func
        if(commandList[0] == preCommand + "_abort"):
            q.put(1)
            seq_command.commandDict[commandList[0]]()
            th.join()
        elif(th != None):
            th.join()

        # Start a subThread with received command
        # commandDict is a dict with keys = "kal_****" and values is function object
        th = Thread(target = seq_command.commandDict[commandList[0]], kwargs = args)
        th.start()

        preCommand = commandList[0]

    conn.close()
    socket.close()
    print("%.6f"%(time.time()), "Server off")
