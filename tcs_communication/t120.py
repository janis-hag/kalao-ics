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
from tcs_communication.pyipc import pymod_libipc as ipc
#import tcs_communication.pygop as gop

from kalao.utils import database

timeout   = 2

host      = "glslogin2.ls.eso.org"
symb_name = "inter"
rcmd      = "ipcsrv"
port      = 12345
semkey    = 1000

#
# The connection to ipcsrv on <host>:
#

def _t120_print_and_log(log_text):
    '''
    Print out message to stdout and log message

    :param log_text: text to be printed and logged
    :return:
    '''
    print(str(kalao_time.now())+' '+log_text)
    database.store_obs_log({'t120_log': log_text})


def send_offset(alt, az):

    socketId = ipc.init_remote_client(host, symb_name, rcmd, port, semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if(socketId <= 0):
        _t120_print_and_log('Error connecting to T120')
        return -1
    else:
        offset_cmd = '@offset '+str(delta_alt) +' '+str(delta_az)
        ipc.send_cmd(offset_cmd, timeout, timeout)

