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
	print("%.6f"%(time.time()), " command=>", commandList[0], "< arg=",commandList[1:], sep="")

conn.close()
socket.close()
print("%.6f"%(time.time()), "Server off")
