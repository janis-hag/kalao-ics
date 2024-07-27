import dbus

from kalao import ippower, logger
from kalao.hardware import cooling, dm, hw_utils, shutter

from kalao.definitions.enums import (IPPowerStatus, RelayState, ReturnCode,
                                     ShutterStatus)

import config

# See https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html
# For documentation on the API


def _connect_dbus_logind(
) -> tuple[dbus.SystemBus | dbus.SessionBus, dbus.Interface]:
    bus = dbus.SystemBus()

    logind = bus.get_object('org.freedesktop.login1',
                            '/org/freedesktop/login1')

    manager = dbus.Interface(logind, 'org.freedesktop.login1.Manager')

    return bus, manager


def power_off() -> None:
    bus, manager = _connect_dbus_logind()

    manager.PowerOff(False)

    bus.close()


def reboot() -> None:
    bus, manager = _connect_dbus_logind()

    manager.Reboot(False)

    bus.close()


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
