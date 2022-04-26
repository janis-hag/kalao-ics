"""
Modul build:

swig -python pymod_libgop.i
gcc -c -fPIC -Wall -DUSE_STRERROR -DSELECT_CALL -DSYSV -DLINUX ../gop/libgop.c  pymod_libgop_wrap.c -I../gop -I/home/weber/anaconda3/include/python3.6m
ld -shared libgop.o pymod_libgop_wrap.o -o _pymod_libgop.so

Test program:
python testgop.py

rem: the tcsproxy comes from gvanuc01:/opt/import/MOCS-master/python/mocs/telescope
"""

import pymod_libgop
import select
#
# rem about GOP: the variable global gop_errno is called: "pymod_libgop.cvar.gop_errno"
#
# definition of the connection structure (gc) the allocation is done in pymod_libgop
#
gc = 0;


#**********************************************************
#* GOP connection     	      	      	      	      	  *
#**********************************************************
#
# - initialize the base socket
# - do the registration on "processes"
# - accept connection on unix socket called "opcuacli"
#
def initializeGopConnection():
  #
  # init the gc structure 
  #
  global gc
  gc = pymod_libgop.gop_alloc_connect_structure()
  pymod_libgop.gop_init_server_socket_unix(
    gc,       	  # connect struct
    "opcuacli",   # symbolic name
    "opcuacli",   # socket name
    1024,     	  # packet size
    4,	      	  # verbosity (0..9)
    0)      	  # timeout [s]
  #
  # create the socket
  #
  status = pymod_libgop.gop_init_connection(gc)
  if status != 0:
    print ("gop_accept_connection: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())
  #
  # registration on "processes" (T4 observation software)
  #
  pymod_libgop.gop_process_registration("opcuacli", -1, "opcuacli", -1, -1)
  #
  # wait for client (normally inter-t120)
  #
  status = pymod_libgop.gop_accept_connection(gc)
  if status != 0:
    print ("gop_accept_connection: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())
  cd = pymod_libgop.gop_get_cd(gc)
  print ("gop_accept_connection: cd = ", cd)


initializeGopConnection()

answer = "test"
nbBytes = pymod_libgop.gop_read(gc, answer, 1024)
print ("recu: ", nbBytes, " bytes, answer = >",answer, "<");



if nbBytes == -1:
  print ("gop_read_data: status = ", nbBytes,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())

print ("recu: ", nbBytes, " bytes, answer = >",answer, "<");

status = pymod_libgop.gop_write_command(gc, "OK")
if status != 0:
  print ("gop_write_command: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())
