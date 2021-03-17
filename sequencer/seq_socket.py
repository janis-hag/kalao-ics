#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from seq_command import *
import socket

host, port = ('', 5555)

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind((host, port))
print("Server on")

while True:
	socket.listen()
	print("Waiting on connection..")
	conn, address = socket.accept()

	cmd_recv = conn.recv(1)
	cmd_recv = int(cmd_recv.decode("utf8"))

	# Execute the command received
	# cmd_dict is define in seq_command
	cmd_dict[cmd_recv]()


conn.close()
socket.close()
print("Server off")
