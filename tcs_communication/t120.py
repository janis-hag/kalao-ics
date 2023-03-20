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
from sequencer import system

# Read config file
parser = ConfigParser()
config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
parser.read(config_path)

#timeout   = 2

#host      = "glslogin1.ls.eso.org"
#symb_name = "inter"
#rcmd      = "ipcsrv"
#port      = 12345
#semkey    = 1000

#host = parser.get('T120', 'Host')
symb_name = parser.get('T120', 'symb_name')
rcmd = parser.get('T120', 'rcmd')
port = parser.getint('T120', 'Port')  # only for inet connection
semkey = parser.getint('T120', 'semkey')  # only for inet connection
connection_timeout = parser.getint(
        'T120', 'connection_timeout')  # only for inet connection
altaz_timeout = parser.getint('T120', 'altaz_timeout')
focus_timeout = parser.getint('T120', 'focus_timeout')
focus_offset_limit = parser.getint(
        'T120', 'focus_offset_limit')  # only for inet connection

#
# The connection to ipcsrv on <host>:
#


def _t120_print_and_log(log_text):
    """
    Print out message to stdout and log message

    :param log_text: text to be printed and logged
    :return:
    """
    print(str(kalao_time.now()) + ' ' + log_text)
    database.store_obs_log({'t120_log': log_text})


def send_offset(delta_az, delta_alt):

    host = database.get_latest_record(
            'obs_log', key='t120_host')['t120_host'] + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, symb_name, rcmd, port, semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        _t120_print_and_log('Error connecting to T120')
        return -1

    _t120_print_and_log(f'Sending {delta_az=} and {delta_alt=} offsets')

    offset_cmd = '@offset ' + str(delta_az) + ' ' + str(delta_alt)
    ipc.send_cmd(offset_cmd, connection_timeout, altaz_timeout)

    return socketId


def send_focus_offset(focus_offset):

    #if focus_offset > focus_offset_limit:
    #    system.print_and_log(f'ERROR, set_focus value {focus_offset} above limit {focus_offset_limit}')

    host = database.get_latest_record(
            'obs_log', key='t120_host')['t120_host'] + '.ls.eso.org'

    #Verify offset value below limit differentiate between offsets and absolute values
    if type(focus_offset) is str:
        if focus_offset[0] == '+' and float(focus_offset) > 2:
            print(f'Error set_focus value out of bounds: {focus_offset}')
            return -1
        elif focus_offset[0] == '-' and float(focus_offset) < -2:
            print(f'Error set_focus value out of bounds: {focus_offset}')
            return -1

    if focus_offset > 30 or focus_offset < 20:
        print(f'Error set_focus value out of bounds: {focus_offset}')
        return -1

    socketId = ipc.init_remote_client(host, symb_name, rcmd, port, semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        _t120_print_and_log('Error connecting to T120')
        return -1

    _t120_print_and_log(f'Sending focus {focus_offset}')

    offset_cmd = '@m2p ' + str(focus_offset)
    ipc.send_cmd(offset_cmd, connection_timeout, focus_timeout)

    return socketId


def get_focus_value():

    host = database.get_latest_record(
            'obs_log', key='t120_host')['t120_host'] + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, symb_name, rcmd, port, semkey)

    print("wait")
    status = ipc.shm_wait(connection_timeout)
    print("ipc.shm_wait returns:", status)
    if (status < 0):
        ipc.shm_free()
        return -1

    print("ini_shm_kw")
    ipc.ini_shm_kw()

    print("put_shm_kw 1")
    ipc.put_shm_kw("COMMAND", "@kal_getm2")

    ipc.shm_ack()
    ipc.shm_wack(focus_timeout)

    returnList = ipc.get_shm_kw("te.m2z")

    ipc.shm_free()

    print(returnList[1])
    _t120_print_and_log(f'Received focus value {returnList[1]}')

    return float(returnList[1])


def test_connection():

    _t120_print_and_log(f'Sending show i')

    host = database.get_latest_record(
            'obs_log', key='t120_host')['t120_host'] + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, symb_name, rcmd, port, semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        _t120_print_and_log('Error connecting to T120')
        return -1

    ipc.send_cmd('show i', connection_timeout, connection_timeout)

    return socketId


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
