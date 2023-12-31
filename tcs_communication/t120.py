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

import json
import time

import pandas as pd

from kalao import database, euler, logger

import requests
import requests.exceptions

from tcs_communication.pyipc import pymod_libipc as ipc

from kalao.definitions.enums import ReturnCode, T120ServerStatus

import config


def send_altaz_offset(delta_alt_arcsec, delta_az_arcsec):
    """
    Send altitude azimuth offset to T120 telescope server.

    :param delta_alt_arcsec: altitude offset to apply
    :param delta_az_arcsec: azimuth offset to apply
    :return:
    """

    host = database.get_last_value('obs', 't120_host') + '.ls.eso.org'

    #print ("ipc.init_remote_client, returns:",socketId)
    # if (socketId <= 0):
    #     logger.error('t120', f'Error connecting to T120')
    #     return -1

    logger.info('t120',
                f'Sending {delta_az_arcsec} and {delta_alt_arcsec} offsets')

    params = {'az_arcsec': delta_az_arcsec, 'el_arcsec': delta_alt_arcsec}

    rValue, resp = _send_request('tracking/offset', params)

    # resp.json() has the format:
    # {'b_alarmed': False, 's_currentStatus': 'Offset correctly sent'}

    # Offsets are corrections to pointing error, not actual change of the center of the field
    # _update_db_ra_dec_offsets(delta_alt_arcsec, delta_az_arcsec)

    return rValue, resp


def send_focus_offset(focus_offset):
    """
    Send focus offset to the T120 telescope server. Values can either be interpreted as relative offsets if with a
    leading +/-, or absolute if the value is only a number.

    :param focus_offset: absolute or relative focus offset to apply
    :return:
    """

    #if focus_offset > focus_offset_limit:
    #    logger.error('t120', f'set_focus value {focus_offset} above limit {focus_offset_limit}')

    #Verify offset value below limit differentiate between offsets and absolute values
    if type(focus_offset) is str:
        if focus_offset[0] == '+' and float(focus_offset) > 200:
            logger.error('t120',
                         f'set_focus value out of bounds: {focus_offset}')
            return -1
        elif focus_offset[0] == '-' and float(focus_offset) < -200:
            logger.error('t120',
                         f'set_focus value out of bounds: {focus_offset}')
            return -1

        new_position = get_focus_value() + focus_offset

    else:
        new_position = focus_offset

    if new_position > 35000 or new_position < 25000:
        logger.error('t120', f'set_focus value out of bounds: {new_position}')
        return -1

    logger.info('t120', f'Sending focus {new_position}')

    #params = {"position": 32000}
    params = {"position": new_position}

    rValue, resp = _send_request('/m2/focus', params)

    # print(resp.json())
    # {'b_alarmed': False, 'b_busy': True, 'b_enabled': False, 's_currentStatus': 'Wait for M2 Power supply stabilizated'}

    return rValue, resp


def update_fo_delta(focus_offset):

    #if focus_offset > focus_offset_limit:
    #    logger.error('t120', f'set_focus value {focus_offset} above limit {focus_offset_limit}')

    host = database.get_last_value('obs', 't120_host') + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        logger.error('t120', 'Error connecting to T120')
        return -1

    logger.info('t120', f'Updating focus offset value fo.delta {focus_offset}')

    offset_cmd = 'fo.delta=' + str(focus_offset)
    ipc.send_cmd(offset_cmd, config.T120.connection_timeout,
                 config.T120.focus_timeout)

    return socketId


def get_focus_value():
    '/m2/status'

    rValue, resp = _send_request('/m2/status')

    logger.info('t120', f'Received focus value {resp["z"]}')

    position = resp['z']
    # Position format: 31997.12426757813

    return position


def request_autofocus():

    host = database.get_last_value('obs', 't120_host') + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        logger.error('t120', 'Error connecting to T120')
        return -1

    logger.info('t120', 'Requesting autofocus.')

    autofocus_cmd = '@t120_autofocus "kalao"'
    ipc.send_cmd(autofocus_cmd, config.T120.connection_timeout,
                 config.T120.focus_timeout)

    return socketId


def test_connection():
    """
    Test de connection to the T120 telecope server

    :return:
    """
    logger.info('t120', 'Testing connection using "show i"')

    host = database.get_last_value('obs', 't120_host') + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)

    if (socketId <= 0):
        logger.error('t120', 'Error connecting to T120')
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

    database.store('obs', {
        'telescope_ra': coord.ra.deg,
        'telescope_dec': coord.dec.deg
    })

    return 0


def get_tube_temp():
    return pd.read_csv(config.T120.temperature_file, sep='\t',
                       header=0).iloc[-1]


def _send_request(request_path, params={}):
    # Clean params
    for key, value in list(params.items()):
        if value is None:
            del params[key]

    if config.T120.dummy_telescope:
        if request_path == 'acquire':
            time.sleep(2)

        return ReturnCode.T120_OK, {}

    else:
        headers = {
            "Content-Type": "application/json",
            "Authorization": "ETCS_API_TOKEN_2023"
        }

        url = f'http://{config.T120.ip}:{config.T120.http_port}/{request_path}'

        try:
            if params == {}:
                req = requests.get(url, timeout=config.T120.request_timeout,
                                   headers=headers)
            else:
                req = requests.post(url, json=params,
                                    timeout=config.T120.request_timeout,
                                    headers=headers)
        except requests.exceptions.ConnectionError:
            return ReturnCode.T120_SERVER_DOWN, None

        try:
            data = json.loads(req.text)
        except Exception:
            data = req.text

        if req.status_code == 200:
            return ReturnCode.T120_OK, data
        else:
            text = f' {data}'

            logger.error(
                't120',
                f'Telescope server answered with an Error {req.status_code}.{text}'
            )

            return ReturnCode.T120_ERROR, data


def check_server_status():
    """
    Verify if the T120 server is up and running and check if the camera can be queried.

    :return: status of the camera server (UP/DOWN/ERROR)
    """

    try:
        r = requests.get(f'http://{config.T120.ip}:{config.T120.port}/')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return T120ServerStatus.DOWN
    except requests.exceptions.HTTPError:
        return T120ServerStatus.ERROR
    else:
        return T120ServerStatus.UP
