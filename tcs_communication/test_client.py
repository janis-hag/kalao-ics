# test_server.py
#
import sys, os
import logging
import time
import socket

# sys.path.append("/home/weber/src/pymod_libgop/")
from tcs_communication.pygop import tcs_srv_gop

# import pymod_libgop
#
# sys.path.append("/home/weber/src/tcs_srv/")
#
# import tcs_srv_gop

#
# Initialise Gop (Geneva Observatory Protocol)
#
gop = tcs_srv_gop.gop()
socketName = "test_server"
socketPort = 18234  # only for inet connection
socketHost = "localhost"  # only for inet connection
#
verbosity = 3
gop.processesRegistration(socketName)
print("%.6f" % (time.time()), "Connection to existing server ...")

#gc = gop.initializeClientGopConnection(socketName, verbosity)
gc = gop.initializeInetClientGopConnection(socketName, socketHost, socketPort,
                                           verbosity)
#
# Infinite loop, waiting for command type on the keybord
# send them an wait for an acknoledgement
#
# quit or exit to end
#
while (True):
    print("")
    print("%.6f" % (time.time()), "Command to send :")
    command = input()
    if ((command == "quit") or (command == "exit")):
        print("%.6f" % (time.time()), "Bye bye")
        break
    #
    # send the command
    #
    gop.write(command)
    print("%.6f" % (time.time()), "Read  Acknowledge")
    command = gop.read()
    print("%.6f" % (time.time()), "AFter gop.read() := ", command)
    if (command == -1):
        print("%.6f" % (time.time()), "Server is dead => exit")
        break
    print("%.6f" % (time.time()), "Receive() := ", command)

#
# in case of break, we disconnect all serveurs
#
print("%.6f" % (time.time()), socketName, " close gop connection and exit")
gop.closeConnection()
sys.exit(0)
