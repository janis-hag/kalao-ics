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
from datetime import datetime, timezone

from kalao import logger

import dbus

from kalao.definitions.enums import ReturnCode, ServiceAction

import config

# See https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.systemd1.html
# For documentation on the API


def connect_dbus_systemd(
    system: bool = False
) -> tuple[dbus.SystemBus | dbus.SessionBus, dbus.Interface]:
    if system:
        bus = dbus.SystemBus()
    else:
        bus = dbus.SessionBus()

    systemd = bus.get_object('org.freedesktop.systemd1',
                             '/org/freedesktop/systemd1')

    manager = dbus.Interface(systemd, 'org.freedesktop.systemd1.Manager')

    return bus, manager


def get_status(unit: str, system: bool = False) -> tuple[str, str, datetime]:
    bus, manager = connect_dbus_systemd(system)

    service = bus.get_object('org.freedesktop.systemd1',
                             object_path=manager.LoadUnit(unit))

    interface = dbus.Interface(
        service, dbus_interface='org.freedesktop.DBus.Properties')

    state = str(interface.Get('org.freedesktop.systemd1.Unit', 'ActiveState'))
    substate = str(interface.Get('org.freedesktop.systemd1.Unit', 'SubState'))
    timestamp = interface.Get('org.freedesktop.systemd1.Unit',
                              'StateChangeTimestamp')

    # Convert Unix microseconds timestamp into datetime object
    timestamp = datetime.fromtimestamp(
        int(timestamp) * 10**(-6), tz=timezone.utc)

    bus.close()

    return state, substate, timestamp


def is_enabled(unit: str, system: bool = False) -> bool | None:
    bus, manager = connect_dbus_systemd(system)

    enabled = str(manager.GetUnitFileState(unit))

    bus.close()

    if enabled == 'enabled':
        return True
    elif enabled == 'disabled':
        return False
    else:
        return None


def is_active(unit: str, system: bool = False) -> bool:
    state, substate, timestamp = get_status(unit, system)

    if state == 'active':
        return True
    else:
        return False


def get_all_status() -> dict[str, tuple[str, str, datetime]]:
    status_dict = {}
    for service in config.Systemd.services.values():
        unit = service['unit']
        system = service.get('system', False)

        status_dict[unit] = get_status(unit, system=system)

    return status_dict


def check_all_active() -> dict[str, bool]:
    status_dict = {}

    for service in config.Systemd.services.values():
        if not service['enabled']:
            continue

        unit = service['unit']
        system = service.get('system', False)

        status_dict[unit] = is_active(unit, system=system)

    return status_dict


def unit_control(unit: str, action: ServiceAction, system: bool = False,
                 runtime_only: bool = False, force: bool = True,
                 mode: str = 'replace', whom: str = "all",
                 signal: int = signal.SIGKILL) -> tuple[str, str, datetime]:
    """
    Function to control systemd unit services.

    :param unit_name: Name of the systemd unit service to control
    :param action: RESTART/START/STOP/STATUS
    :return:
    """

    if action != ServiceAction.STATUS:
        logger.info('services', f'Sending {action} command to {unit}.')

    bus, manager = connect_dbus_systemd(system)

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
        logger.error('services', f'Unknown action: {action}')
        return 'unknown', 'unknown', datetime.fromtimestamp(0, tz=timezone.utc)

    bus.close()

    return get_status(unit)


def init() -> ReturnCode:
    '''
    Initialise all system services and run sanity checks

    :return:
    '''

    for service in config.Systemd.services.values():
        unit = service['unit']
        system = service.get('system', False)

        if system:
            continue

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

    for unit, status in all_statuses.items():
        if not status:
            logger.error('services', f'{unit} is down!')

    if not all(all_statuses.values()):
        logger.error('services', 'One or more services are not running!')
        return ReturnCode.SERVICES_ERROR

    return ReturnCode.SERVICES_OK
