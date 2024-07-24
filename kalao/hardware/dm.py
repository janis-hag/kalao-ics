import time

from kalao import database, ippower, logger
from kalao.cacao import toolbox
from kalao.cacao.aocontrol import reset_dm

from kalao.definitions.enums import IPPowerStatus, ReturnCode

import config


def on() -> ReturnCode:
    logger.info('wfs', 'Turning on DM')

    if ippower.get_status(config.IPPower.Port.DM) == IPPowerStatus.OFF:
        logger.info('dm', 'Powering on DM ippower')

        # Prevent inactivity checks from turning DM off immediately
        database.store('obs', {'deadman_keepalive': -1})
        time.sleep(1)

        ret = ippower.switch(config.IPPower.Port.DM, IPPowerStatus.ON)

        if ret != IPPowerStatus.ON:
            logger.error('dm', 'Failed to power on DM ippower')
            return ReturnCode.GENERIC_ERROR

        time.sleep(config.Hardware.dm_wait_between_actions)

    bmc_display_fps = toolbox.get_fps(config.FPS.BMC)

    if bmc_display_fps is not None:
        if not bmc_display_fps.run_isrunning():
            logger.info('dm', f'Starting {config.FPS.BMC}')

            # Prevent inactivity checks from turning DM off immediately
            database.store('obs', {'deadman_keepalive': -1})
            time.sleep(1)

            bmc_display_fps.run_start()

            time.sleep(config.Hardware.dm_wait_between_actions)

            reset_dm(config.AO.DM_loop_number)

        if not bmc_display_fps.run_isrunning():
            logger.error('dm', f'Unable to start {config.FPS.BMC}')

            return ReturnCode.GENERIC_ERROR

    return ReturnCode.OK


def off() -> ReturnCode:
    logger.info('dm', 'Turning off DM')

    logger.info('dm', 'Resetting DM')
    reset_dm(config.AO.DM_loop_number)

    time.sleep(config.Hardware.dm_wait_between_actions)

    bmc_display_fps = toolbox.get_fps(config.FPS.BMC)
    if bmc_display_fps is not None:
        logger.info('dm', f'Stopping {config.FPS.BMC}')
        bmc_display_fps.run_stop()

        time.sleep(config.Hardware.dm_wait_between_actions)

    logger.info('dm', 'Powering off DM ippower')
    ret = ippower.switch(config.IPPower.Port.DM, IPPowerStatus.OFF)

    if ret == IPPowerStatus.OFF:
        return ReturnCode.OK
    else:
        return ReturnCode.GENERIC_ERROR
