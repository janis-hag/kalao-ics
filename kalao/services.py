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

import signal
import time
from datetime import datetime

from kalao.utils import database

import dbus

from kalao.definitions.enums import ServiceAction

import config

# See https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.systemd1.html
# For documentation on the API


def connect_dbus(system=False):
    if system:
        bus = dbus.SystemBus()
    else:
        bus = dbus.SessionBus()

    systemd = bus.get_object('org.freedesktop.systemd1',
                             '/org/freedesktop/systemd1')

    manager = dbus.Interface(systemd, 'org.freedesktop.systemd1.Manager')

    return bus, systemd, manager


def get_status(unit, system=False):
    bus, systemd, manager = connect_dbus(system)

    service = bus.get_object('org.freedesktop.systemd1',
                             object_path=manager.LoadUnit(unit))

    interface = dbus.Interface(
        service, dbus_interface='org.freedesktop.DBus.Properties')

    state = str(interface.Get('org.freedesktop.systemd1.Unit', 'ActiveState'))
    substate = str(interface.Get('org.freedesktop.systemd1.Unit', 'SubState'))
    timestamp = interface.Get('org.freedesktop.systemd1.Unit', 'StateChangeTimestamp')

    # Convert Unix microseconds timestamp into datetime object
    timestamp = datetime.utcfromtimestamp(int(timestamp) * 10**(-6))

    bus.close()

    return state, substate, timestamp


def is_enabled(unit, system=False):
    bus, systemd, manager = connect_dbus(system)

    enabled = str(manager.GetUnitFileState(unit))

    bus.close()

    if enabled == 'enabled':
        return True
    elif enabled == 'disabled':
        return False
    else:
        return None


def is_active(unit, system=False):
    state, substate, timestamp = get_status(unit, system)

    if state == 'active':
        return True
    else:
        return False


def get_all_status():
    status_dict = {}
    for service in config.Systemd.services.values():
        unit = service['unit']

        status_dict[unit] = get_status(unit)

    return status_dict


def check_all_active():
    status_dict = {}

    for service in config.Systemd.services.values():
        if not service['enabled']:
            continue

        unit = service['unit']

        status_dict[unit] = is_active(unit)

        if not status_dict[unit]:
            database.store('obs',
                           {'services_log': f'[WARNING] {unit} is down!'})

    return status_dict


def unit_control(unit, action, runtime_only=False, force=True, mode='replace',
                 whom="all", signal=signal.SIGKILL, system=False):
    """
    Function to control systemd unit services.

    :param unit_name: Name of the systemd unit service to control
    :param action: RESTART/START/STOP/STATUS
    :return:
    """

    if action != ServiceAction.STATUS:
        database.store('obs', {
            'services_log': f'Sending {action} command to {unit}.'
        })

    bus, systemd, manager = connect_dbus(system)

    if action == ServiceAction.STATUS:
        # Status is always returned as long as the action keyword is correct
        pass
    elif action == ServiceAction.START:
        job = manager.StartUnit(unit, mode)
    elif action == ServiceAction.STOP:
        job = manager.StopUnit(unit, mode)
    elif action == ServiceAction.RESTART:
        job = manager.RestartUnit(unit, mode)
    elif action == ServiceAction.RELOAD:
        job = manager.ReloadUnit(unit, mode)
    elif action == ServiceAction.KILL:
        job = manager.KillUnit(unit, whom, int(signal))
    elif action == ServiceAction.ENABLE:
        carries_install_info, changes = manager.EnableUnitFiles([unit],
                                                                runtime_only,
                                                                force)
    elif action == ServiceAction.DISABLE:
        changes = manager.DisableUnitFiles([unit], runtime_only)
    else:
        database.store('obs',
                       {'services_log': f'[ERROR] Unknown action: {action}'})
        return -1

    bus.close()

    return get_status(unit)


def camera(action):
    return unit_control(config.Systemd.services['camera']['unit'], action)


def flask(action):
    return unit_control(config.Systemd.services['flask-gui']['unit'], action)


def gop(action):
    return unit_control(config.Systemd.services['gop-server']['unit'], action)


def database_timer(action):
    return unit_control(config.Systemd.services['database-timer']['unit'],
                        action)


def safety_timer(action):
    return unit_control(config.Systemd.services['safety-timer']['unit'],
                        action)


def loop_timer(action):
    return unit_control(config.Systemd.services['loop-timer']['unit'], action)


def pump_timer(action):
    return unit_control(config.Systemd.services['pump-timer']['unit'], action)


def init():
    '''
    Initialise all system services and run sanity checks

    :return:
    '''

    system_setup_active = is_active('kalao_system-setup.service', system=True)

    if not system_setup_active:
        database.store('obs', {
            'services_log': f'[ERROR] kalao_system-setup.service is down!'
        })

    for service in config.Systemd.services.values():
        unit = service['unit']

        if service['enabled']:
            if not is_enabled(unit):
                unit_control(unit, ServiceAction.ENABLE)

            if service['restart']:
                unit_control(unit, ServiceAction.RESTART)
            elif not is_active(unit):
                unit_control(unit, ServiceAction.START)
        else:
            if is_enabled(unit):
                unit_control(unit, ServiceAction.DISABLE)

            if is_active(unit):
                unit_control(unit, ServiceAction.STOP)

    time.sleep(config.Systemd.service_restart_wait)

    all_statuses = check_all_active()

    if not all(all_statuses.values()):
        database.store('obs', {
            'services_log': f'[ERROR] One or more services are not running!'
        })
        return -1

    return 0
