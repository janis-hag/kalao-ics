#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : system.py
# @Date : 2021-08-16-13-33
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
system.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import time
from datetime import datetime

import dbus

from kalao.utils import database

import kalao_config as config
from kalao_enums import SequencerStatus


def _isDigit(x):
    try:
        float(x)
        return True
    except ValueError:
        return False


def check_active(unit_name):
    #unit_name = 'kalao_database_updater.service'

    bus, systemd, manager = connect_dbus()

    service = bus.get_object('org.freedesktop.systemd1',
                             object_path=manager.GetUnit(unit_name))

    interface = dbus.Interface(
            service, dbus_interface='org.freedesktop.DBus.Properties')
    active_state = str(
            interface.Get('org.freedesktop.systemd1.Unit', 'ActiveState'))

    if active_state == 'active':
        active_entertimestamp = interface.Get('org.freedesktop.systemd1.Unit',
                                              'ActiveEnterTimestamp')
    else:
        active_entertimestamp = interface.Get('org.freedesktop.systemd1.Unit',
                                              'ActiveExitTimestamp')

    active_substate = str(
            interface.Get('org.freedesktop.systemd1.Unit', 'SubState'))

    # Convert Unix microseconds timestamp into datetime object
    active_entertimestamp = datetime.utcfromtimestamp(
            int(active_entertimestamp) * 10**(-6))

    bus.close()

    return active_state, active_substate, active_entertimestamp


def check_enabled(unit_name):
    #unit_name = 'kalao_database_updater.service'

    bus, systemd, manager = connect_dbus()

    enabled_state = manager.GetUnitFileState(unit_name)

    bus.close()

    return enabled_state


def unit_control(unit_name, action):
    """
    Function to control systemd unit services.

    :param unit_name: Name of the systemd unit service to control
    :param action: RESTART/START/STOP/STATUS
    :return:
    """
    bus, systemd, manager = connect_dbus()

    action = action.upper()

    if action == 'RESTART':
        job = manager.RestartUnit(unit_name, 'replace')
    elif action == 'START':
        job = manager.StartUnit(unit_name, 'replace')
    elif action == 'STOP':
        job = manager.StopUnit(unit_name, 'replace')
    elif action == 'STATUS':
        # Status is always returned as long as the action keyword is correct
        pass
    else:
        error_string = ("ERROR: system.unit_control unknown action: " +
                        str(action))
        print(error_string)
        database.store_obs_log({'sequencer_log': error_string})
        return -1

    bus.close()

    return check_active(unit_name)


# def restart_unit(unit_name):
#
#     bus, systemd, manager = connect_dbus()
#     #manager.EnableUnitFiles([‘picockpit - client.service’], False, True)
#     #manager.Reload()
#     job = manager.RestartUnit(unit_name, 'replace')
#
#     return job
#
#
# def start_unit(unit_name):
#
#     bus, systemd, manager = connect_dbus()
#     #manager.EnableUnitFiles([‘picockpit - client.service’], False, True)
#     #manager.Reload()
#     job = manager.StartUnit(unit_name, 'replace')
#
#     return job
#
#
# def stop_unit(unit_name):
#
#     bus, systemd, manager = connect_dbus()
#     #manager.EnableUnitFiles([‘picockpit - client.service’], False, True)
#     #manager.Reload()
#     job = manager.StopUnit(unit_name)
#
#     return job


def connect_dbus():
    bus = dbus.SessionBus()
    systemd = bus.get_object('org.freedesktop.systemd1',
                             '/org/freedesktop/systemd1')

    manager = dbus.Interface(systemd, 'org.freedesktop.systemd1.Manager')

    return bus, systemd, manager


def check_status():
    return_status = {
            'camera_service': True,
            'database_service': True,
            'flask_service': True
    }

    camera_status = camera_service('status')
    if not camera_status[0] == 'active':
        database.store_obs_log({'fli_log': 'WARNING: Camera service down!'})
        return_status['camera_service'] = False

    database_status = database_service('status')
    if not database_status[0] == 'active':
        database.store_obs_log({
                'database_log': 'WARNING: Database service down!'
        })
        return_status['database_service'] = False

    flask_status = flask_service('status')
    if not flask_status[0] == 'active':
        database.store_obs_log({
                'flask_log': 'WARNING: Flask GUI server down!'
        })
        return_status['flask_service'] = False

    return return_status


def camera_service(action):
    """
    Control the camera server systemd service. It accepts one of the four systemctl commands:
    RESTART/START/STOP/STATUS

    :param action: RESTART/START/STOP/STATUS
    :return:
    """

    if not action.upper() == 'STATUS':
        database.store_obs_log({
                'fli_log':
                        'Sending ' + action + ' command to FLI camera server.'
        })
    unit_name = config.SystemD.camera_service
    status = unit_control(unit_name, action)

    return status


def database_service(action):
    """
    Control the database systemd service. It accepts one of the four systemctl commands:
    RESTART/START/STOP/STATUS

    :param action: RESTART/START/STOP/STATUS
    :return:
    """

    if not action.upper() == 'STATUS':
        database.store_obs_log({
                'database_log':
                        'Sending ' + action + ' command to database system.'
        })
    unit_name = config.SystemD.database_updater
    status = unit_control(unit_name, action)

    return status


def flask_service(action):
    """
    Control the flask server systemd service. It accepts one of the four systemctl commands:
    RESTART/START/STOP/STATUS

    :param action: RESTART/START/STOP/STATUS
    :return:
    """

    if not action.upper() == 'STATUS':
        database.store_obs_log({
                'flask_log': 'Sending ' + action + ' command to flask server.'
        })
    unit_name = config.SystemD.flask_gui
    status = unit_control(unit_name, action)

    return status


def gop_service(action):
    if not action.upper() == 'STATUS':
        database.store_obs_log({
                'gop_log': 'Sending ' + action + ' command to gop server.'
        })
    unit_name = config.SystemD.gop_server
    status = unit_control(unit_name, action)

    return status


def watchdog_service(action):
    """
    Control the flask server systemd service. It accepts one of the four systemctl commands:
    RESTART/START/STOP/STATUS

    :param action: RESTART/START/STOP/STATUS
    :return:
    """

    if not action.upper() == 'STATUS':
        database.store_obs_log({
                'flask_log':
                        'Sending ' + action + ' command to safety watchdog.'
        })
    unit_name = config.SystemD.safety_watchdog
    status = unit_control(unit_name, action)

    return status


def initialise_services():
    '''
    Initialise all system services and run sanity checks

    :return:
    '''

    database_service('restart')
    camera_service('restart')
    flask_service('restart')
    gop_service('restart')
    watchdog_service('restart')

    time.sleep(config.SystemD.service_restart_wait)

    # Loop as long as not all systems are active.
    if not all(check_status().values()):
        database.store_obs_log({
                'sequencer_log':
                        'ERROR: a service is not running! ' +
                        str(check_status())
        })
        database.store_obs_log({'sequencer_status': SequencerStatus.ERROR})
        return -1

    return 0


def print_and_log(message):
    print(message)
    database.store_obs_log({'sequencer_log': message})
