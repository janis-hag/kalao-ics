from functools import wraps
from typing import Any, Callable

import dasbus.client.proxy
import dasbus.connection

from kalao import ippower, logger
from kalao.hardware import cooling, dm, hw_utils, shutter

from kalao.definitions.enums import (IPPowerStatus, RelayState, ReturnCode,
                                     ShutterStatus)

import config

# See https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html
# For documentation on the API


class Logind:
    def _connect_to_system_bus(self):
        self._system_bus = dasbus.connection.SystemMessageBus()
        self._system_manager = dasbus.client.proxy.InterfaceProxy(
            self._system_bus, 'org.freedesktop.login1',
            '/org/freedesktop/login1', 'org.freedesktop.login1.Manager')

    def manager(self) -> dasbus.client.proxy.InterfaceProxy:
        if not hasattr(self, '_system_manager'):
            self._connect_to_system_bus()

        return self._system_manager

    def close(self) -> None:
        if hasattr(self, '_system_manager'):
            dasbus.client.proxy.disconnect_proxy(self._system_manager)

        if hasattr(self, '_system_bus'):
            self._system_bus.disconnect()


def autoconnect(fun: Callable) -> Callable:
    @wraps(fun)
    def wrapper(*args: Any, system: bool = False, logind: Logind | None = None,
                **kwargs: Any) -> Any:
        ret = None
        exception = None

        if logind is None:
            disconnect_on_exit = True
            logind = Logind()
        else:
            disconnect_on_exit = False

        try:
            ret = fun(*args, logind=logind, **kwargs)
        except Exception as e:
            exception = e

        if disconnect_on_exit:
            logind.close()

        if exception is not None:
            raise exception

        return ret

    return wrapper


@autoconnect
def power_off(logind: Logind = None) -> None:
    logind.manager().PowerOff(False)


@autoconnect
def reboot(logind: Logind = None) -> None:
    logind.manager().Reboot(False)


def shutdown_sequence() -> None:
    logger.info('rtc', 'Initiating shutdown sequence')

    # Close shutter
    if shutter.close() != ShutterStatus.CLOSED:
        logger.error('rtc', 'Failed to close shutter')

    # Shut down DM
    if dm.off() != ReturnCode.OK:
        logger.error('rtc', 'Failed to turn off DM')

    # Turn off lamps
    if hw_utils.lamps_off() != ReturnCode.OK:
        logger.error('rtc', 'Failed to turn off lamps')

    # Warm cameras
    # Not needed currently

    # Shut down bench
    if ippower.switch(config.IPPower.Port.Bench,
                      IPPowerStatus.OFF) != IPPowerStatus.OFF:
        logger.error('rtc', 'Failed to turn off bench')

    # Stop cooling system
    if cooling.heater_off() != RelayState.OFF:
        logger.error('rtc', 'Failed to turn off heater')

    if cooling.pump_off() != RelayState.OFF:
        logger.error('rtc', 'Failed to turn off pump')

    if cooling.heatexchanger_fan_off() != RelayState.OFF:
        logger.error('rtc', 'Failed to turn off heat exchanger fan')

    # Shut down computer
    logger.info('rtc', 'Shutdown sequence over, powering off')
    power_off()
