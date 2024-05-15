import time

from kalao import database, ippower, logger
from kalao.cacao import toolbox
from kalao.cacao.aocontrol import reset_dm

from kalao.definitions.enums import IPPowerStatus, ReturnCode

import config


def on() -> ReturnCode:
    if ippower.status(config.IPPower.Port.DM) == IPPowerStatus.OFF:
        logger.info('dm', 'Powering on DM ippower')

        # Prevent inactivity checks from turning DM off immediately
        database.store('obs', {'deadman_keepalive': 0})
        time.sleep(1)

        ret = ippower.switch(config.IPPower.Port.DM, IPPowerStatus.ON)

        if ret != IPPowerStatus.ON:
            logger.error('dm', f'Failed to power on DM ippower')
            return ReturnCode.GENERIC_ERROR

        time.sleep(config.Timers.dm_wait_between_actions)

    bmc_display_fps = toolbox.open_fps_once(config.FPS.BMC)

    if bmc_display_fps is not None:
        if not bmc_display_fps.run_runs():
            logger.info('dm', f'Starting {config.FPS.BMC}')

            # Prevent inactivity checks from turning DM off immediately
            database.store('obs', {'deadman_keepalive': 0})
            time.sleep(1)

            bmc_display_fps.run_start()

            time.sleep(config.Timers.dm_wait_between_actions)

            reset_dm(config.AO.DM_loop_number)

        if not bmc_display_fps.run_runs():
            logger.error('dm', f'Unable to start {config.FPS.BMC}')

            return ReturnCode.GENERIC_ERROR

    return ReturnCode.OK


def off() -> ReturnCode:
    logger.info('dm', 'Turning off DM')

    logger.info('dm', 'Resetting DM')
    reset_dm(config.AO.DM_loop_number)

    time.sleep(config.Timers.dm_wait_between_actions)

    bmc_display_fps = toolbox.open_fps_once(config.FPS.BMC)
    if bmc_display_fps is not None:
        logger.info('dm', f'Stopping {config.FPS.BMC}')
        bmc_display_fps.run_stop()

        time.sleep(config.Timers.dm_wait_between_actions)

    logger.info('dm', 'Powering off DM ippower')
    ret = ippower.switch(config.IPPower.Port.DM, IPPowerStatus.OFF)

    if ret == IPPowerStatus.OFF:
        return ReturnCode.OK
    else:
        return ReturnCode.GENERIC_ERROR
