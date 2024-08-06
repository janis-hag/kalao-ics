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
from functools import wraps
from typing import Any, Callable

import dbus

from kalao import logger

from kalao.definitions.enums import ReturnCode, ServiceAction

import config

# See https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.systemd1.html
# For documentation on the API


class Systemd:
    def _connect_to_system_bus(self):
        self._system_bus = dbus.SystemBus()
        self._system_systemd = self._system_bus.get_object(
            'org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        self._system_manager = dbus.Interface(
            self._system_systemd, 'org.freedesktop.systemd1.Manager')

    def _connect_to_session_bus(self):
        self._session_bus = dbus.SessionBus()
        self._session_systemd = self._session_bus.get_object(
            'org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        self._session_manager = dbus.Interface(
            self._session_systemd, 'org.freedesktop.systemd1.Manager')

    def bus(self, system: bool) -> dbus.SystemBus | dbus.SessionBus:
        if system:
            if not hasattr(self, '_system_bus'):
                self._connect_to_system_bus()

            return self._system_bus
        else:
            if not hasattr(self, '_session_bus'):
                self._connect_to_session_bus()

            return self._session_bus

    def manager(self, system: bool) -> dbus.Interface:
        if system:
            if not hasattr(self, '_system_manager'):
                self._connect_to_system_bus()

            return self._system_manager
        else:
            if not hasattr(self, '_session_manager'):
                self._connect_to_session_bus()

            return self._session_manager

    def close(self):
        if hasattr(self, '_system_bus'):
            self._system_bus.close()

        if hasattr(self, '_session_bus'):
            self._session_bus.close()


def autoconnect(fun: Callable) -> Callable:
    @wraps(fun)
    def wrapper(*args: Any, systemd: Systemd | None = None,
                **kwargs: Any) -> Any:
        ret = None
        exception = None

        if systemd is None:
            disconnect_on_exit = True
            systemd = Systemd()
        else:
            disconnect_on_exit = False

        try:
            ret = fun(*args, systemd=systemd, **kwargs)
        except Exception as e:
            exception = e

        if disconnect_on_exit:
            systemd.close()

        if exception is not None:
            raise exception

        return ret

    return wrapper


@autoconnect
def get_status(unit: str, system: bool = False,
               systemd: Systemd = None) -> tuple[str, str, datetime]:
    service = systemd.bus(system).get_object(
        'org.freedesktop.systemd1',
        object_path=systemd.manager(system).LoadUnit(unit))

    interface = dbus.Interface(
        service, dbus_interface='org.freedesktop.DBus.Properties')

    state = str(interface.Get('org.freedesktop.systemd1.Unit', 'ActiveState'))
    substate = str(interface.Get('org.freedesktop.systemd1.Unit', 'SubState'))
    timestamp = interface.Get('org.freedesktop.systemd1.Unit',
                              'StateChangeTimestamp')

    # Convert Unix microseconds timestamp into datetime object
    timestamp = datetime.fromtimestamp(
        int(timestamp) * 10**(-6), tz=timezone.utc)

    return state, substate, timestamp


@autoconnect
def is_enabled(unit: str, system: bool = False,
               systemd: Systemd = None) -> bool | None:
    enabled = str(systemd.manager(system).GetUnitFileState(unit))

    if enabled == 'enabled':
        return True
    elif enabled == 'disabled':
        return False
    else:
        return None


def is_active(unit: str, system: bool = False,
              systemd: Systemd = None) -> bool:
    state, substate, timestamp = get_status(unit, system, systemd=systemd)

    if state == 'active':
        return True
    else:
        return False


@autoconnect
def get_all_status(systemd: Systemd = None
                   ) -> dict[str, tuple[str, str, datetime]]:
    status_dict = {}
    for service in config.Systemd.services.values():
        unit = service['unit']
        system = service.get('system', False)

        status_dict[unit] = get_status(unit, system=system, systemd=systemd)

    return status_dict


@autoconnect
def check_all_active(systemd: Systemd = None) -> dict[str, bool]:
    status_dict = {}

    for service in config.Systemd.services.values():
        if not service['enabled']:
            continue

        unit = service['unit']
        system = service.get('system', False)

        status_dict[unit] = is_active(unit, system=system, systemd=systemd)

    return status_dict


@autoconnect
def unit_control(unit: str, action: ServiceAction, system: bool = False,
                 runtime_only: bool = False, force: bool = True,
                 mode: str = 'replace', whom: str = 'all',
                 signal: int = signal.SIGKILL,
                 systemd: Systemd = None) -> tuple[str, str, datetime]:
    """
    Function to control systemd unit services.
    """

    if action != ServiceAction.STATUS:
        logger.info('services', f'Sending {action} command to {unit}.')

    manager = systemd.manager(system)

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

    return get_status(unit)


def init() -> ReturnCode:
    '''
    Initialise all system services and run sanity checks
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
