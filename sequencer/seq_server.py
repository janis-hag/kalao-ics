#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import seq_command
import seq_init
import socket
import time

#seq_init.initialisation()

host, port = ('', 5555)

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind((host, port))
print("%.6f"%(time.time()), "Server on")

while True:
	socket.listen()
	print("%.6f"%(time.time()), "Waiting on connection..")
	conn, address = socket.accept()

	command = (conn.recv(256)).decode("utf8")

	separator 	= command[0]
	command 	= command[1:]
	commandList = command.split(separator)
	#
	# 'command' is commandList[0], 'arguments' are commandList[1:]
	#
	print("%.6f"%(time.time()), " command=>", commandList[0], "< arg=",commandList[1:], sep="")

	# commandDict is a dict with keys = "kal_****" and values is function object
	command_seq.commandDict[commandList[0]](commandList[1:])

conn.close()
socket.close()
print("%.6f"%(time.time()), "Server off")
