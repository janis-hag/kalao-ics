#
# use: 
#
# glslogin2: inter -server -echo
#
# glslogin1:
#
# 	bash
#	cd ~/src/pymod_libipc
#	python test_offset.py
#
# sort 10 ligne de "show i" sur glslogin2
#	
import sys
import time
#sys.path.append("/home/weber/src/pymod_libipc/")
#sys.path.append("/home/weber/src/pymod_libgop/")
import pymod_libipc as ipc
import pygop as gop

timeout   = 2

host      = "glslogin2"
symb_name = "inter"
rcmd      = "ipcsrv"
port      = 12345
semkey    = 1000

#
# The connection to ipcsrv on <host>:
#
socketId = ipc.init_remote_client(host, symb_name, rcmd, port, semkey)
print ("ipc.init_remote_client, returns:",socketId)
if(socketId <= 0):
  print ("No connection, exit")
  sys.exit(-1)


for x in range(10):
  print ("send: show i")
  ipc.send_cmd("show i", timeout, timeout)

for x in range(10):
  print ("send: show j")
  ipc.send_cmd("show j", timeout, timeout)

