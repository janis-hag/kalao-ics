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
#import sys
#import time
#sys.path.append("/home/weber/src/pymod_libipc/")
#sys.path.append("/home/weber/src/pymod_libgop/")

import os

from pathlib import Path
from configparser import ConfigParser

from tcs_communication.pyipc import pymod_libipc as ipc
#import tcs_communication.pygop as gop

from kalao.utils import database, kalao_time

# Read config file
parser = ConfigParser()
config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
parser.read(config_path)

#timeout   = 2

#host      = "glslogin1.ls.eso.org"
#symb_name = "inter"
#rcmd      = "ipcsrv"
#port      = 12345
#semkey    = 1000

host = parser.get('T120', 'Host')
symb_name = parser.get('T120', 'symb_name')
rcmd = parser.get('T120', 'rcmd')
port = parser.getint('T120', 'Port')  # only for inet connection
semkey = parser.getint('T120', 'semkey')  # only for inet connection
timeout = parser.getint('T120', 'timeout')  # only for inet connection


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


def send_offset(delta_alt, delta_az):

    _t120_print_and_log(f'Sending {delta_alt} and {delta_az} offsets')


    socketId = ipc.init_remote_client(host, symb_name, rcmd, port, semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if(socketId <= 0):
        _t120_print_and_log('Error connecting to T120')
        return -1

    offset_cmd = '@offset '+str(delta_alt) +' '+str(delta_az)
    ipc.send_cmd(offset_cmd, timeout, timeout)

    return ipc


def test_connection():

    _t120_print_and_log(f'Sending show i')


    socketId = ipc.init_remote_client(host, symb_name, rcmd, port, semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if(socketId <= 0):
        _t120_print_and_log('Error connecting to T120')
        return -1

    ipc.send_cmd('show i', timeout, timeout)

    return ipc


# def get_status():
#     _t120_print_and_log(f'Sending {delta_alt} and {delta_az} offsets')
#     socketId = ipc.init_remote_client(host, symb_name, rcmd, port, semkey)
#     # print ("ipc.init_remote_client, returns:",socketId)
#     if (socketId <= 0):
#         _t120_print_and_log('Error connecting to T120')
#         return -1
#     else:
#         #status_cmd = '@offset ' + str(delta_alt) + ' ' + str(delta_a)
#         #ipc.send_cmd(offset_cmd, timeout, timeout)
#
#
#         print ("wait");
#         status = ipc.shm_wait(timeout)
#         print ("ipc.shm_wait returns:", status)
#         if (status<0):
#           ipc.shm_free()
#           sys.exit(-1)
#
#         print ("ini_shm_kw");
#         ipc.ini_shm_kw()
#
#         print ("put_shm_kw COMMAND");
#         ipc.put_shm_kw("COMMAND","@t120_get_positions")
#
#         print ("shmack");
#         ipc.shm_ack()
#         print ("shmwack");
#         ipc.shm_wack()
#         #
#         # returns: ob.alpha ob.delta te.alpcons te.delcons scrmesuazi scrmesuele cupposmes
#         #
#         print ("get_shm_kw");
#         returnList = ipc.get_shm_kw("scrmesuazi")
#         azi = returnList[1]
#         print ("get_shm_kw");
#         returnList = ipc.get_shm_kw("scrmesuele")
#         ele = returnList[1]
#
#         print("azi=",azi,"ele=",ele," <======================================")
#
#         print ("shmfree");
#         ipc.shm_free()
