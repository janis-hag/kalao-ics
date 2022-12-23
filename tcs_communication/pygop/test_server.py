# test_server.py
#
import sys, os
import logging
import time
import socket

sys.path.append("/home/weber/src/pymod_libgop/")

import pymod_libgop

sys.path.append("/home/weber/src/tcs_srv/")

import tcs_srv_gop

#
# Initialise Gop (Geneva Observatory Protocol)
#
gop = tcs_srv_gop.gop()
socketName = "test_server"
socketPort = 18234  # only for inet connection
#
verbosity = 3
gop.processesRegistration(socketName)

print("%.6f" % (time.time()),
      "Initialize new gop connection. Wait for client ...")
#gc = gop.initializeGopConnection(socketName, verbosity)
gc = gop.initializeInetGopConnection(socketName, socketPort, verbosity)
#
# Infinite loop, waiting for command
# Rem; all command reply an acknowledgement
#
while (True):
    print("")
    print("%.6f" % (time.time()), "Wait for command")
    #
    # read and parse the input string
    #
    command = gop.read()
    print("%.6f" % (time.time()), "After gop.read() := ", command)
    if (command == -1):
        print("%.6f" % (time.time()),
              "Initialize new gop connection. Wait for client ...")
        gc = gop.initializeInetGopConnection(socketName, verbosity)
        continue  # go to beginning

    separator = command[0]
    command = command[1:]
    commandList = command.split(separator)
    command = commandList[0]
    #
    # 'command' is commandList[0], 'arguments' are commandList[1:]
    #
    print("%.6f" % (time.time()), " command=>", command, "< arg=",
          commandList[1:], sep="")
    #
    # Manage the command. 2 cases:
    # - its a state machine (with a nodeId wich starts with "ns=")
    # - its a local command (test, exit, ...)
    #

    if (command == "test"):
        message = "/OK"
        print("%.6f" % (time.time()), "Send acknowledge: ", message)
        gop.write(message)
    elif ((command == "quit") or (command == "exit")):
        message = "/OK"
        print("%.6f" % (time.time()), "Send acknowledge and quit: ", message)
        gop.write(message)
        print("%.6f" % (time.time()), "Acknowledge sended")
        break
    else:
        message = "/OK"
        print("%.6f" % (time.time()), "Send acknowledge: ", message)
        gop.write(message)

#
# in case of break, we disconnect all serveurs
#
print("%.6f" % (time.time()), socketName, " close gop connection and exit")
gop.closeConnection()
sys.exit(0)
