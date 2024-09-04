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

import dasbus.client.proxy
import dasbus.connection

from kalao.common.enums import ReturnCode, ServiceAction

from kalao.ics import logger

import config

# See https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.systemd1.html
# For documentation on the API


class Systemd:
    def _connect_to_system_bus(self):
        self._system_bus = dasbus.connection.SystemMessageBus()
        self._system_manager = dasbus.client.proxy.InterfaceProxy(
            self._system_bus, 'org.freedesktop.systemd1',
            '/org/freedesktop/systemd1', 'org.freedesktop.systemd1.Manager')

    def _connect_to_session_bus(self):
        self._session_bus = dasbus.connection.SessionMessageBus()
        self._session_manager = dasbus.client.proxy.InterfaceProxy(
            self._session_bus, 'org.freedesktop.systemd1',
            '/org/freedesktop/systemd1', 'org.freedesktop.systemd1.Manager')

    def bus(self, system: bool) -> dasbus.connection.MessageBus:
        if system:
            if not hasattr(self, '_system_bus'):
                self._connect_to_system_bus()

            return self._system_bus
        else:
            if not hasattr(self, '_session_bus'):
                self._connect_to_session_bus()

            return self._session_bus

    def manager(self, system: bool) -> dasbus.client.proxy.InterfaceProxy:
        if system:
            if not hasattr(self, '_system_manager'):
                self._connect_to_system_bus()

            return self._system_manager
        else:
            if not hasattr(self, '_session_manager'):
                self._connect_to_session_bus()

            return self._session_manager

    def close(self):
        if hasattr(self, '_system_manager'):
            dasbus.client.proxy.disconnect_proxy(self._system_manager)

        if hasattr(self, '_system_bus'):
            self._system_bus.disconnect()

        if hasattr(self, '_session_manager'):
            dasbus.client.proxy.disconnect_proxy(self._session_manager)

        if hasattr(self, '_session_bus'):
            self._session_bus.disconnect()


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
    interface = dasbus.client.proxy.InterfaceProxy(
        systemd.bus(system), 'org.freedesktop.systemd1',
        systemd.manager(system).LoadUnit(unit),
        'org.freedesktop.DBus.Properties')

    state = interface.Get('org.freedesktop.systemd1.Unit',
                          'ActiveState').get_string()
    substate = interface.Get('org.freedesktop.systemd1.Unit',
                             'SubState').get_string()
    timestamp = interface.Get('org.freedesktop.systemd1.Unit',
                              'StateChangeTimestamp').get_uint64()

    dasbus.client.proxy.disconnect_proxy(interface)

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
