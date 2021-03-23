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
socketPort = 18234    # only for inet connection
#
verbosity = 3
gop.processesRegistration(socketName)

print("%.6f"%(time.time()), "Initialize new gop connection. Wait for client ...")
#gc = gop.initializeGopConnection(socketName, verbosity)
gc = gop.initializeInetGopConnection(socketName, socketPort, verbosity)
#
# Infinite loop, waiting for command
# Rem; all command reply an acknoledgement
#
while (True):
  print("")
  print("%.6f"%(time.time()), "Wait for command")
  #
  # read and parse the input string
  #
  command     = gop.read()
  print ("%.6f"%(time.time()), "AFter gop.read() := ", command)
  if(command == -1):
    print("%.6f"%(time.time()), "Initialize new gop connection. Wait for client ...")
    gc = gop.initializeGopConnection(socketName, verbosity)
    continue    # go to beginning

  seperator   = command[0]
  command     = command[1:]
  commandList = command.split(seperator)
  #
  # 'command' is commandList[0], 'arguments' are commandList[1:]
  #
  print ("%.6f"%(time.time()), " command=>", command, "< arg=",commandList[1:], sep="")

  # Check if its a KalAO command and send it
  if(commandList[0][:3] == "kal"):
    hostSeq, portSeq = ('localhost', 5555)
    socketSeq = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
      socketSeq.connect((hostSeq,portSeq))
      print("%.6f"%(time.time()), "Connected to sequencer")

      commandKal = seperator + command
      socketSeq.sendall(commandKal.encode("utf8"))
      print("%.6f"%(time.time()), "Command sent")

    except ConnectionRefusedError:
      print("%.6f"%(time.time()), "Error: connection to sequencer refused")
    finally:
      socketSeq.close()

  #
  # Manage the command. 2 cases:
  # - its a state machine (with a nodeId wich starts with "ns=")
  # - its a local command (test, exit, ...)
  #

  if (command == "test"):
    message = "/OK"
    print("%.6f"%(time.time()), "Send acknoledge: ", message)
    gop.write(message)
  elif ((command == "quit") or (command == "exit")):
    message = "/OK"
    print("%.6f"%(time.time()), "Send acknoledge and quit: ", message)
    gop.write(message)
    print("%.6f"%(time.time()), "Acknoledge sended")
    break
  else:
    message = "/OK"
    print("%.6f"%(time.time()), "Send acknoledge: ", message)
    gop.write(message)

#
# in case of break, we disconnect all serveurs
#
print ("%.6f"%(time.time()), socketName, " close gop connection and exit")
gop.closeConnection()
sys.exit(0)
