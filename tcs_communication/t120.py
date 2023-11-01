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

import pandas as pd



from tcs_communication.pyipc import pymod_libipc as ipc
#import tcs_communication.pygop as gop

from kalao import euler
from kalao.utils import database, kalao_time

import kalao_config as config

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


def send_offset(delta_alt_arcsec, delta_az_arcsec):
    """
    Send altitude azimuth offset to T120 telescope server.

    :param delta_alt_arcsec: altitude offset to apply
    :param delta_az_arcsec: azimuth offset to apply
    :return:
    """

    host = database.get_latest_record(
            'obs_log', key='t120_host')['t120_host'] + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        _t120_print_and_log('Error connecting to T120')
        return -1

    _t120_print_and_log(
            f'Sending {delta_az_arcsec=} and {delta_alt_arcsec=} offsets')

    offset_cmd = '@offset ' + str(delta_az_arcsec) + ' ' + str(delta_alt_arcsec)
    ipc.send_cmd(offset_cmd, config.T120.connection_timeout,
                 config.T120.altaz_timeout)

    # Offsets are corrections to pointing error, not actual change of the center of the field
    # _update_db_ra_dec_offsets(delta_alt_arcsec, delta_az_arcsec)

    return socketId


def send_focus_offset(focus_offset):
    """
    Send focus offset to the T120 telescope server. Values can either be interpreted as relative offsets if with a
    leading +/-, or absolute if the value is only a number.

    :param focus_offset: absolute or relative focus offset to apply
    :return:
    """

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

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        _t120_print_and_log('Error connecting to T120')
        return -1

    _t120_print_and_log(f'Sending focus {focus_offset}')

    offset_cmd = '@m2p ' + str(focus_offset)
    ipc.send_cmd(offset_cmd, config.T120.connection_timeout,
                 config.T120.focus_timeout)

    return socketId


def update_fo_delta(focus_offset):

    #if focus_offset > focus_offset_limit:
    #    system.print_and_log(f'ERROR, set_focus value {focus_offset} above limit {focus_offset_limit}')

    host = database.get_latest_record(
            'obs_log', key='t120_host')['t120_host'] + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        _t120_print_and_log('Error connecting to T120')
        return -1

    _t120_print_and_log(f'Updating focus offset value fo.delta {focus_offset}')

    offset_cmd = 'fo.delta=' + str(focus_offset)
    ipc.send_cmd(offset_cmd, config.T120.connection_timeout,
                 config.T120.focus_timeout)

    return socketId


def get_focus_value():

    host = database.get_latest_record(
            'obs_log', key='t120_host')['t120_host'] + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)

    print("wait")
    status = ipc.shm_wait(config.T120.connection_timeout)
    print("ipc.shm_wait returns:", status)
    if (status < 0):
        ipc.shm_free()
        return -1

    print("ini_shm_kw")
    ipc.ini_shm_kw()

    print("put_shm_kw 1")
    ipc.put_shm_kw("COMMAND", "@kal_getm2")

    ipc.shm_ack()
    ipc.shm_wack(config.T120.focus_timeout)

    returnList = ipc.get_shm_kw("te.m2z")

    ipc.shm_free()

    print(returnList[1])
    _t120_print_and_log(f'Received focus value {returnList[1]}')

    return float(returnList[1])


def request_autofocus():
    host = database.get_latest_record(
            'obs_log', key='t120_host')['t120_host'] + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        _t120_print_and_log('Error connecting to T120')
        return -1

    _t120_print_and_log(f'Requesting autofocus.')

    autofocus_cmd = '@t120_autofocus "kalao"'
    ipc.send_cmd(autofocus_cmd, config.T120.connection_timeout,
                 config.T120.focus_timeout)

    return socketId


def test_connection():
    """
    Test de connection to the T120 telecope server

    :return:
    """
    _t120_print_and_log(f'Sending show i')

    host = database.get_latest_record(
            'obs_log', key='t120_host')['t120_host'] + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        _t120_print_and_log('Error connecting to T120')
        return -1

    ipc.send_cmd('show i', config.T120.connection_timeout,
                 config.T120.connection_timeout)

    return socketId


def _update_db_ra_dec_offsets(delta_alt_arcsec, delta_az_arcsec):
    """
    Update the telescope RA/DEC values in the database to take into account the new offsets

    :param delta_alt_offset: alt offset which has been sent to the telescope
    :param delta_az_offset: az offset which has been sent to the telescope
    :return:
    """

    # TODO convert alt/az offset into ra/dec
    coord = euler.compute_altaz_offset(delta_alt_arcsec, delta_az_arcsec)

    database.store_obs_log({'telescope_ra': coord.ra.value})
    database.store_obs_log({'telescope_dec': coord.dec.value})

    return 0


def get_tube_temp():
    return pd.read_csv(config.T120.temperature_file, sep='\t',
                       header=0).iloc[-1]


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
