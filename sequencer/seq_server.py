#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import seq_command
import seq_init
import socket
import time

from itertools import zip_longest

host, port = ('', 5555)

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind((host, port))
print("%.6f"%(time.time()), "Server on")

while True:
	socket.listen()
	print("%.6f"%(time.time()), "Waiting on connection..")
	conn, address = socket.accept()

	command = (conn.recv(4096)).decode("utf8")

	separator 	= command[0]
	command 	= command[1:]
	commandList = command.split(separator)
	#
	# 'command' is commandList[0], 'arguments' are commandList[1:]
	#
	print("%.6f"%(time.time()), " command=>", commandList[0], "< arg=",commandList[1:], sep="")

	# Transform list of arg to a dict
	argDict = dict(zip_longest(*[iter(commandList[1:])] * 2, fillvalue=""))

	# commandDict is a dict with keys = "kal_****" and values is function object
	seq_command.commandDict[commandList[0]](argDict)

conn.close()
socket.close()
print("%.6f"%(time.time()), "Server off")
