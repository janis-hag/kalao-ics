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


def connect_dbus():
    bus = dbus.SessionBus()
    systemd = bus.get_object('org.freedesktop.systemd1',
                             '/org/freedesktop/systemd1')

    manager = dbus.Interface(systemd, 'org.freedesktop.systemd1.Manager')

    return bus, systemd, manager


def check_active(unit_name):
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
    bus, systemd, manager = connect_dbus()

    enabled_state = manager.GetUnitFileState(unit_name)

    bus.close()

    return enabled_state


def check_status():
    return_status = {}

    for service in config.SystemD.services.items():
        status = _generic_service(service, 'status')
        if not status[0] == 'active':
            database.store_obs_log({
                    service['log']: f'WARNING: {service["unit"]} down!'
            })
            return_status[service['unit']] = False
        else:
            return_status[service['unit']] = True

    return return_status


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


def _generic_service(service, action):
    if not action.upper() == 'STATUS':
        database.store_obs_log({
                service['log']:
                        f'Sending {action} command to {service["unit"]}.'
        })
    status = unit_control(f'{service["unit"]}', action)

    return status


def camera_service(action):
    return _generic_service(config.SystemD.services['camera'])


def flask_service(action):
    return _generic_service(config.SystemD.services['flask'])


def gop_service(action):
    return _generic_service(config.SystemD.services['gop'])


def database_timer_service(action):
    return _generic_service(config.SystemD.services['database'])


def safety_timer_service(action):
    return _generic_service(config.SystemD.services['safety'])


def loop_timer_service(action):
    return _generic_service(config.SystemD.services['loop'])


def pump_timer_service(action):
    return _generic_service(config.SystemD.services['pump'])


def initialise_services():
    '''
    Initialise all system services and run sanity checks

    :return:
    '''

    for service in config.SystemD.services.items():
        _generic_service(service, 'restart')

    time.sleep(config.SystemD.service_restart_wait)

    all_statuses = check_status()

    # Loop as long as not all systems are active.
    if not all(all_statuses.values()):
        database.store_obs_log({
                'sequencer_log':
                        f'ERROR: one or more services are not running! {all_statuses}'
        })
        database.store_obs_log({'sequencer_status': SequencerStatus.ERROR})
        return -1

    return 0


def print_and_log(message):
    print(message)
    database.store_obs_log({'sequencer_log': message})
