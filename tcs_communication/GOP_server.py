# test_server.py
#
import os
import sys
import time
import socket
from pathlib import Path
from configparser import ConfigParser

# Read config file
parser = ConfigParser()
config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
parser.read(config_path)

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from kalao.interface import status

import pymod_libgop

import tcs_srv_gop

#
# Initialise Gop (Geneva Observatory Protocol)
#
gop = tcs_srv_gop.gop()
socketName = parser.get('GOP','IP')
socketPort = parser.getint('GOP','Port')  # only for inet connection
#
verbosity = parser.getint('GOP','Verbosity')
gop.processesRegistration(socketName)

print("%.6f" % (time.time()), "Initialize new gop connection. Wait for client ...")
# gc = gop.initializeGopConnection(socketName, verbosity)
gc = gop.initializeInetGopConnection(socketName, socketPort, verbosity)
#
# Infinite loop, waiting for command
# Rem; all command reply an acknowledgement
#
while (True):
    print("")
    print("%.6f" % (time.time()), "Wait for command")
    #
    # read and concat until "#" char, then parse the input string
    #
    command = ""
    controlRead = ""
    while '#' not in controlRead:
        #  '#' signe used to signify end of command
        controlRead = gop.read()

        if (controlRead == -1):
            print("%.6f" % (time.time()), "Initialize new gop connection. Wait for client ...")
            # gc = gop.initializeGopConnection(socketName, verbosity)
            gc = gop.initializeInetGopConnection(socketName, socketPort, verbosity)
            break

        command += controlRead  # concat input string

    if (controlRead == -1):
        continue  # go to beginning

    print("%.6f" % (time.time()), "After gop.read() := ", command)

    seperator = command[0]
    command = command[1:]
    commandList = command.split(seperator)
    #
    # 'command' is commandList[0], 'arguments' are commandList[1:]
    #
    print("%.6f" % (time.time()), " command=>", commandList[0], "< arg=", commandList[1:], sep="")

    # Check if its a KalAO command and send it
    if (commandList[0][:3] == "kal"):

        host = parser.get('SEQ', 'IP')
        port = parser.getint('SEQ', 'Port')

        hostSeq, portSeq = (host, port)
        socketSeq = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            socketSeq.connect((hostSeq, portSeq))
            print("%.6f" % (time.time()), "Connected to sequencer")

            commandKal = seperator + command
            socketSeq.sendall(commandKal.encode("utf8"))
            print("%.6f" % (time.time()), "Command sent")

        except ConnectionRefusedError:
            print("%.6f" % (time.time()), "Error: connection to sequencer refused")
        finally:
            socketSeq.close()

    #
    # Manage the command. 2 cases:
    # - its a state machine (with a nodeId wich starts with "ns=")
    # - its a local command (test, exit, ...)
    #

    if commandList[0] == "test":
        message = "/OK"
        print("%.6f" % (time.time()), "Send acknowledge: ", message)
        gop.write(message)
    elif ((commandList[0] == "quit") or (commandList[0] == "exit")):
        message = "/OK"
        print("%.6f" % (time.time()), "Send acknowledge and quit: ", message)
        gop.write(message)
        print("%.6f" % (time.time()), "Acknowledge sent")
        break
    elif commandList[0] == "status":
        message = status.kalao_status()
        print("%.6f" % (time.time()), "Send status: ", message)
        gop.write(message)
    else:
        message = "/OK"
        print("%.6f" % (time.time()), "Send acknowledge: ", message)
        gop.write(message)
#
# in case of break, we disconnect all servers
#
print("%.6f" % (time.time()), socketName, " close gop connection and exit")
gop.closeConnection()
sys.exit(0)
