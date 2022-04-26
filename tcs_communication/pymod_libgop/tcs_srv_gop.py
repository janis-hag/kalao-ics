# tcs_srv_gop.py  -- Communication avec GenevaObservatoryProtocol -- Telescope Control System server
#
#   
import sys
import logging
import time
import .pymod_libgop
#
# This class interface few fonctionnalities of GOP
# GOP is written in C and the wrapper made by swig
#
# rem about GOP: the variable global gop_errno is called: "pymod_libgop.cvar.gop_errno"
#
class gop():

  gc = 0    # pointer to a gop_connection structure (allocated in libgop.c(pymod_libgop))
  
#  
### METHODS ####################################################################
#
#-------------------------------------------------------------------------------        
  def initializeGopConnection(self, myName, verbosity):
    #
    # - initialize the base socket type Unix (base on file)
    # - accept connection on unix socket called <myName>
    #
    self.gc = pymod_libgop.gop_alloc_connect_structure()
    pymod_libgop.gop_init_server_socket_unix(
      self.gc,    # connect struct
      myName,     # symbolic name
      myName,     # socket name
      1024,       # packet size
      verbosity,  # verbosity (0..9)
      0)      	  # timeout [s]
    #
    # create the socket
    #
    status = pymod_libgop.gop_init_connection(self.gc)
    if status != 0:
      print ("%.6f"%(time.time()), "gop_accept_connection: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())
    #
    # wait for client (normally inter-t120)
    #
    status = pymod_libgop.gop_accept_connection(self.gc)
    if status != 0:
      print ("%.6f"%(time.time()), "gop_accept_connection: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())

    cd = pymod_libgop.gop_get_cd(self.gc)
    print ("%.6f"%(time.time()), "gop_accept_connection: cd = ", cd)
  
    return (self.gc)
    
#-------------------------------------------------------------------------------        
  def initializeClientGopConnection(self, myName, verbosity):
    #
    # - initialize the base socket type unix (based on file)
    #
    self.gc = pymod_libgop.gop_alloc_connect_structure()
    pymod_libgop.gop_init_client_socket_unix(
      self.gc,    # connect struct
      myName,     # symbolic name
      myName,     # socket name
      1024,       # packet size
      verbosity,  # verbosity (0..9)
      0)      	  # timeout [s]
    #
    # create the socket
    #
    #status = pymod_libgop.gop_init_connection(self.gc)
    #if status != 0:
    #  print ("%.6f"%(time.time()), "gop_connection: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())
    #
    # Connect on existing server
    #
    status = pymod_libgop.gop_connection(self.gc)
    if status != 0:
      print ("%.6f"%(time.time()), "gop_connection: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())

    cd = pymod_libgop.gop_get_cd(self.gc)
    print ("%.6f"%(time.time()), "gop_connection: cd = ", cd)
  
    return (self.gc)
    
#-------------------------------------------------------------------------------        
  def initializeInetGopConnection(self, myName, port, verbosity):
    #
    # - initialize the base socket type Inet (based on port number)
    # - accept connection on unix socket called <myName>
    #
    self.gc = pymod_libgop.gop_alloc_connect_structure()
    pymod_libgop.gop_init_server_socket(
      self.gc,    # connect struct
      myName,     # symbolic name
      port,       # socket port
      1024,       # packet size
      verbosity,  # verbosity (0..9)
      0)      	  # timeout [s]
    #
    # create the socket
    #
    status = pymod_libgop.gop_init_connection(self.gc)
    if status != 0:
      print ("%.6f"%(time.time()), "gop_accept_connection: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())
    #
    # wait for client (normally inter-t120)
    #
    status = pymod_libgop.gop_accept_connection(self.gc)
    if status != 0:
      print ("%.6f"%(time.time()), "gop_accept_connection: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())

    cd = pymod_libgop.gop_get_cd(self.gc)
    print ("%.6f"%(time.time()), "gop_accept_connection: cd = ", cd)
  
    return (self.gc)
    
#-------------------------------------------------------------------------------        
  def initializeInetClientGopConnection(self, myName, host, port, verbosity):
    #
    # - initialize the base socket type unix (based on port number)
    #
    self.gc = pymod_libgop.gop_alloc_connect_structure()
    pymod_libgop.gop_init_client_socket(
      self.gc,    # connect struct
      myName,     # symbolic name
      host,       # socket host
      port,       # socket port
      1024,       # packet size
      verbosity,  # verbosity (0..9)
      0)      	  # timeout [s]
    #
    # create the socket
    #
    #status = pymod_libgop.gop_init_connection(self.gc)
    #if status != 0:
    #  print ("%.6f"%(time.time()), "gop_connection: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())
    #
    # Connect on existing server
    #
    status = pymod_libgop.gop_connection(self.gc)
    if status != 0:
      print ("%.6f"%(time.time()), "gop_connection: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())

    cd = pymod_libgop.gop_get_cd(self.gc)
    print ("%.6f"%(time.time()), "gop_connection: cd = ", cd)
  
    return (self.gc)
    
#-------------------------------------------------------------------------------        
  def processesRegistration(self, myName):
     #
    # registration on "processes" (T4 observation software)
    #
    pymod_libgop.gop_process_registration(myName, -1, myName, -1, -1)
  
#-------------------------------------------------------------------------------        
  def getConnectionStructure(self):
    return (self.gc)  
    
#-------------------------------------------------------------------------------        
  def getErrStr(self):
    return (pymod_libgop.gop_get_error_str())
  
#-------------------------------------------------------------------------------        
  def getErrNo(self):
    return (pymod_libgop.cvar.gop_errno)
    
#-------------------------------------------------------------------------------        
  def read(self):
    #
    # read socket, be carefull, with the wrapper, the result is given if the returnList:
    # - returnList[0] = size of return message
    # - returnList[1] = return message
    #
    answer  = "x" * 1024  # answer must be allocated, if not we get a segmentation violation
    maxsize = 1024
    returnList = pymod_libgop.gop_read(self.gc, answer, maxsize)
    if returnList[0] <= 0:
      print ("%.6f"%(time.time()), "ERROR during pymod_libgop.gop_read(): status =", returnList," gop_errno =",gop.getErrNo(self), ":", gop.getErrStr(self))
      return (-1);
    print("%.6f"%(time.time()), " Recu: ", returnList[0], " bytes, answer = >", returnList[1], "<", sep="");
    return returnList[1]
    
#-------------------------------------------------------------------------------        
  def write(self, string):
    #
    # socket write
    #
    status = pymod_libgop.gop_write_command(self.gc, string)
    if status != 0:
      print ("%.6f"%(time.time()), "gop_write_command: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())
    
#-------------------------------------------------------------------------------        
  def closeConnection(self):
    pymod_libgop.gop_close_connection(self.gc)
    
    
"""

#======== BEGIN =======================================================================#
#
# loggin level (more with logging.INFO, more with logging.DEBUG)
#
logging.basicConfig(level=logging.WARN)
#
# Connexion on the serveur OPC-UA on the PLC
#

try:
    client = Client("opc.tcp://10.10.132.66:4840")
    client.connect()
    
    initializeGopConnection()
    #
    # Infinite loop, waiting for command
    #
    while (True):
    answer = "test"
    nbBytes = pymod_libgop.gop_read(gc, answer, 1024)
    if nbBytes <= 0:
        print ("gop_read_data: status = ", nbBytes,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())

    print ("recu: ", nbBytes, " bytes, answer = >",answer, "<");

    status = pymod_libgop.gop_write_command(gc, "OK")
    if status != 0:
        print ("gop_write_command: status = ", status,"  gop_errno = ",pymod_libgop.cvar.gop_errno, " : ", pymod_libgop.gop_get_error_str())


finally:
"""
