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

from kalao import euler
from kalao.utils import database, kalao_time

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
    #     database.store('obs', {'t120_log': 'Error connecting to T120'})
    #     return -1

    database.store('obs', {
        't120_log': f'Sending {delta_az_arcsec} and {delta_alt_arcsec} offsets'
    })

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
    #    system.print_and_log(f'ERROR, set_focus value {focus_offset} above limit {focus_offset_limit}')

    #Verify offset value below limit differentiate between offsets and absolute values
    if type(focus_offset) is str:
        if focus_offset[0] == '+' and float(focus_offset) > 200:
            database.store('obs', {
                't120_log':
                    f'Error set_focus value out of bounds: {focus_offset}'
            })
            return -1
        elif focus_offset[0] == '-' and float(focus_offset) < -200:
            database.store('obs', {
                't120_log':
                    f'Error set_focus value out of bounds: {focus_offset}'
            })
            return -1

    if focus_offset > 3500 or focus_offset < 2500:
        database.store('obs', {
            't120_log': f'Error set_focus value out of bounds: {focus_offset}'
        })
        return -1

    database.store('obs', {'t120_log': f'Sending focus {focus_offset}'})

    new_position = get_focus_value() + focus_offset

    #params = {"position": 32000}
    params = {"position": new_position}

    rValue, resp = _send_request('/m2/focus/', params)

    # print(resp.json())
    # {'b_alarmed': False, 'b_busy': True, 'b_enabled': False, 's_currentStatus': 'Wait for M2 Power supply stabilizated'}

    return rValue, resp


def update_fo_delta(focus_offset):

    #if focus_offset > focus_offset_limit:
    #    system.print_and_log(f'ERROR, set_focus value {focus_offset} above limit {focus_offset_limit}')

    host = database.get_last_value('obs', 't120_host') + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        database.store('obs', {'t120_log': 'Error connecting to T120'})
        return -1

    database.store('obs', {
        't120_log': f'Updating focus offset value fo.delta {focus_offset}'
    })

    offset_cmd = 'fo.delta=' + str(focus_offset)
    ipc.send_cmd(offset_cmd, config.T120.connection_timeout,
                 config.T120.focus_timeout)

    return socketId


def get_focus_value():
    '/m2/status'

    rValue, resp = _send_request('/m2/status/')

    database.store('obs',
                   {'t120_log': f'Received focus value {resp.json()["z"]}'})

    position = resp.json()['z']
    # Position format: 31997.12426757813

    return rValue, position


def request_autofocus():

    host = database.get_last_value('obs', 't120_host') + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)
    #print ("ipc.init_remote_client, returns:",socketId)
    if (socketId <= 0):
        database.store('obs', {'t120_log': 'Error connecting to T120'})
        return -1

    database.store('obs', {'t120_log': 'Requesting autofocus.'})

    autofocus_cmd = '@t120_autofocus "kalao"'
    ipc.send_cmd(autofocus_cmd, config.T120.connection_timeout,
                 config.T120.focus_timeout)

    return socketId


def test_connection():
    """
    Test de connection to the T120 telecope server

    :return:
    """
    database.store('obs', {'t120_log': 'Testing connection using "show i"'})

    host = database.get_last_value('obs', 't120_host') + '.ls.eso.org'

    socketId = ipc.init_remote_client(host, config.T120.symb_name,
                                      config.T120.rcmd, config.T120.port,
                                      config.T120.semkey)

    if (socketId <= 0):
        database.store('obs', {'t120_log': 'Error connecting to T120'})
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

    if not check_server_status() == T120ServerStatus.UP:
        return ReturnCode.T120_SERVER_DOWN, {}

    else:
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
            if params == {}:
                req = requests.get(url, timeout=config.T120.request_timeout,
                                   headers=headers)
            else:
                req = requests.post(url, json=params,
                                    timeout=config.T120.request_timeout,
                                    headers=headers)

            try:
                data = json.loads(req.text)
            except Exception:
                data = req.text

            if req.status_code == 200:
                return ReturnCode.T120_OK, data
            else:
                text = ''

                if data.get('error_text') is not None:
                    text += f' {data.get("error_text")}'

                if data.get('error_status') is not None:
                    text += f' (status = {data.get("error_status")})'

                database.store(
                    'obs', {
                        f'fli_log':
                            f'[ERROR] Telescope server answered with an Error {req.status_code}.{text}'
                    })

                return ReturnCode.T120_ERROR, data


def check_server_status():
    """
    Verify if the T120 server is up and running and check if the camera can be queried.

    :return: status of the camera server (UP/DOWN/ERROR)
    """

    #server_status = services.camera(ServiceAction.STATUS)

    #if server_status[0] == 'inactive':
    #    return T120ServerStatus.DOWN

    return T120ServerStatus.UP
    # Overriding

    try:
        r = requests.get(
            f'http://{config.T120.ip}:{config.T120.http_port}/ping')
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return T120ServerStatus.DOWN
    except requests.exceptions.HTTPError:
        return T120ServerStatus.ERROR
    else:
        return T120ServerStatus.UP
